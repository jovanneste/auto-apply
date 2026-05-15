import json
import re
from typing import Any


# JS injected into the page to traverse shadow DOM and collect form fields
_EXTRACT_FIELDS_JS = """
() => {
  const fields = [];

  function getLabel(el) {
    // 1. <label for="id">
    if (el.id) {
      const lbl = document.querySelector(`label[for="${el.id}"]`);
      if (lbl) return lbl.innerText.trim();
    }
    // 2. ancestor <label>
    const ancestor = el.closest('label');
    if (ancestor) return ancestor.innerText.replace(el.value || '', '').trim();
    // 3. aria-label
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').trim();
    // 4. aria-labelledby
    const lblId = el.getAttribute('aria-labelledby');
    if (lblId) {
      const lblEl = document.getElementById(lblId);
      if (lblEl) return lblEl.innerText.trim();
    }
    // 5. previous sibling text
    let prev = el.previousElementSibling;
    if (prev) return prev.innerText.trim();
    // 6. placeholder
    return el.placeholder || el.name || '';
  }

  function getFieldType(el) {
    const tag = el.tagName.toLowerCase();
    if (tag === 'textarea') return 'textarea';
    if (tag === 'select') return 'select';
    const type = (el.type || 'text').toLowerCase();
    if (type === 'file') return 'file';
    if (type === 'checkbox') return 'checkbox';
    if (type === 'radio') return 'radio';
    if (type === 'date' || type === 'month' || type === 'year') return 'date';
    return 'text';
  }

  function getOptions(el) {
    const tag = el.tagName.toLowerCase();
    if (tag === 'select') {
      return Array.from(el.options)
        .filter(o => o.value)
        .map(o => ({ value: o.value, label: o.text.trim() }));
    }
    // Radio group
    if (el.type === 'radio' && el.name) {
      return Array.from(document.querySelectorAll(`input[type=radio][name="${el.name}"]`))
        .map(r => ({ value: r.value, label: getLabel(r) }));
    }
    return null;
  }

  function isRequired(el) {
    if (el.required) return true;
    if (el.getAttribute('aria-required') === 'true') return true;
    const label = document.querySelector(`label[for="${el.id}"]`);
    if (label && label.innerText.includes('*')) return true;
    return false;
  }

  const seen = new Set();

  function collectFromRoot(root) {
    const selectors = [
      'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image])',
      'textarea',
      'select',
    ];
    root.querySelectorAll(selectors.join(',')).forEach((el, idx) => {
      const key = el.id || el.name || `${el.tagName}-${idx}`;
      if (seen.has(key)) return;
      seen.add(key);

      // Skip radio duplicates (keep only first in group)
      if (el.type === 'radio' && el.name && seen.has(`radio-group-${el.name}`)) return;
      if (el.type === 'radio' && el.name) seen.add(`radio-group-${el.name}`);

      const opts = getOptions(el);
      fields.push({
        field_type: getFieldType(el),
        field_label: getLabel(el),
        field_name: el.name || el.id || null,
        field_placeholder: el.placeholder || null,
        is_required: isRequired(el),
        options_json: opts ? JSON.stringify(opts) : null,
      });
    });

    // Recurse into shadow roots
    root.querySelectorAll('*').forEach(el => {
      if (el.shadowRoot) collectFromRoot(el.shadowRoot);
    });
  }

  collectFromRoot(document);
  return fields;
}
"""


async def extract_fields(page, page_number: int = 1) -> list[dict[str, Any]]:
    """Extract all form fields from the current Playwright page."""
    raw = await page.evaluate(_EXTRACT_FIELDS_JS)

    fields = []
    for i, f in enumerate(raw):
        f["page_number"] = page_number
        f["display_order"] = i
        fields.append(f)

    return fields


async def find_next_button(page):
    """Return the next/continue button element, or None if on last page."""
    patterns = [
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Proceed')",
        "button:has-text('Next Step')",
        "[aria-label*='Next']",
        "input[type=submit][value*='Next']",
        "input[type=submit][value*='Continue']",
    ]
    for selector in patterns:
        btn = page.locator(selector).first
        if await btn.count() > 0:
            try:
                if await btn.is_visible():
                    return btn
            except Exception:
                continue
    return None


async def find_apply_button(page):
    """Return the 'Apply Now' / 'Apply' button if this is a job description page."""
    patterns = [
        "a:has-text('Apply Now')",
        "a:has-text('Apply for this job')",
        "button:has-text('Apply Now')",
        "button:has-text('Apply')",
        "a:has-text('Start Application')",
    ]
    for selector in patterns:
        btn = page.locator(selector).first
        if await btn.count() > 0:
            try:
                if await btn.is_visible():
                    return btn
            except Exception:
                continue
    return None


async def fill_placeholders(page, fields: list[dict]):
    """Fill required fields with placeholder values to pass client-side validation."""
    for f in fields:
        if not f.get("is_required"):
            continue
        name = f.get("field_name")
        ftype = f.get("field_type", "text")
        if not name or ftype == "file":
            continue
        try:
            if ftype in ("text", "textarea"):
                selector = f'[name="{name}"]'
                el = page.locator(selector).first
                if await el.count() > 0 and await el.is_visible():
                    await el.fill("Test")
            elif ftype == "select":
                selector = f'select[name="{name}"]'
                el = page.locator(selector).first
                if await el.count() > 0:
                    opts = f.get("options_json")
                    if opts:
                        import json as _json
                        options = _json.loads(opts)
                        if options:
                            await el.select_option(value=options[0]["value"])
            elif ftype == "radio":
                selector = f'input[type=radio][name="{name}"]'
                el = page.locator(selector).first
                if await el.count() > 0:
                    await el.check()
            elif ftype == "date":
                selector = f'[name="{name}"]'
                el = page.locator(selector).first
                if await el.count() > 0 and await el.is_visible():
                    await el.fill("01/01/1990")
        except Exception:
            pass
