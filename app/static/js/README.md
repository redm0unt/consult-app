# JavaScript Structure

This directory now contains modular client-side code split into shared utilities, reusable UI components, and page-specific initialisers. Scripts are published as ES modules and loaded with `<script type="module">` to enable clean imports.

## Layout

```
app/static/js/
├── main.js                        # Global entry point loaded on every page
├── components/                    # Reusable UI widgets
│   ├── account-menu.js            # Sidebar account dropdown
│   ├── alerts.js                  # Flash messages + dynamic alert factory
│   ├── copy-buttons.js            # Clipboard helpers for [data-copy-text]
│   ├── dropdowns.js               # Generic [data-dropdown] controller
│   └── search.js                  # Search form clear button behaviour
├── pages/
│   └── teachers/
│       ├── grid.js                # Teacher card edit/delete actions
│       ├── import.js              # XLSX import workflow + feedback
│       ├── index.js               # Page bootstrap wired from template
│       └── modal.js               # Create/update teacher modal logic
└── utils/
    └── dom.js                     # Query helpers + shared selectors/constants
```

## Initiation Flow

* `main.js` runs on DOM ready and configures shared interactions (account menu, alerts, copy buttons, search forms).
* Page templates include additional entry points when required. For example, `admin/teachers.html` loads `pages/teachers/index.js`, which wires together dropdowns, modal behaviour, import handling, and grid actions.

## Adding New Behaviour

1. Create helpers inside `utils/` if you expose new low-level DOM operations.
2. Prefer encapsulating UI functionality inside `components/` so it can be reused.
3. For page-specific flows, place an entry module under `pages/<page>/` and load it from the corresponding template with `<script type="module">`.
4. Register new page scripts in templates after calling `{{ super() }}` to ensure the global bundle remains available.

## Testing Checklist

After changing UI logic, manually verify:

- Sidebar account menu toggling and focus handling.
- Auto-dismiss behaviour for flash alerts and copy-to-clipboard buttons.
- Teachers page: search clear button, action dropdowns, modal open/update flows, delete confirmation, import success/error reporting.

Automated UI tests are not yet available; run through the checklist locally before deploying.
