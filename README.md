# Sikorska Notary

The website for Sikorska Notary Limited, a notarial practice in Bristol.
<https://www.sikorskanotary.co.uk>

Plain HTML, CSS and one JavaScript file. **No build step, no framework, no
dependencies, no database.** The folder you are looking at is the website. Copy it
onto a server and it runs.

---

## Where to start

| If you are | Read |
|---|---|
| Putting the site live for the first time | **`HANDOVER.md`** |
| Wondering why a decision was made | ask Liam, the full change record is held by Alchemy |

## Running it locally

```bash
python -m http.server 8123
```

Then open <http://localhost:8123>. That is the whole setup.

---

## Changing the practice's details

**Do not do this by hand.** There is no template, so the header, footer and calls
to action are copied into all eleven pages. The phone number appears in **over 110
places** in three different formats: the `tel:` link, the version people read, and
the structured data Google uses. Missing a few means a notary with a wrong phone
number on some pages, which means lost enquiries.

Use the script:

```bash
python update-details.py                          # show what is set, and where
python update-details.py --phone "07123 456789"   # preview
python update-details.py --phone "07123 456789" --apply
python update-details.py --email new@example.com --apply
```

Nothing is written without `--apply`.

## After editing site.css or site.js

The stylesheet and script are linked with a version on the end:

```html
<link rel="stylesheet" href="assets/css/site.css?v=20260817">
```

That number is what tells browsers to fetch the new file. **Change the file without
changing the number and returning visitors keep the old one, so your change looks
like it did not work.**

```bash
python update-details.py --bump-version --apply
```

Then re-upload the HTML files as well as the changed asset.

---

## Two things not to rewrite

- **`polski.html`** is Patrycja's own writing, not a translation. A Polish client
  can tell the difference immediately, which is the entire point of the page. Do
  not machine translate it or edit it without asking her.
- **Her biography on `practice.html`** is her own words, supplied verbatim.

---

## What is here

```
index.html                        Home
notarial-service.html             Notarial services
apostille-and-legalisation.html   Apostille & legalisation
will-writing-service.html         Will writing
for-business.html                 For business
fees-and-disbursements.html       Fees & disbursements
practice.html                     The Practice: standing, biography, the office
contact.html                      Contact and the enquiry form
polski.html                       Polish language page
legal-and-regulatory.html         Regulatory, complaints, downloadable documents
404.html                          Not found

.htaccess                         Redirects, 404, caching. Apache and Hostinger.
_redirects                        The same rules in Netlify format. Inert on Apache.
robots.txt  sitemap.xml

assets/css/site.css               Every style on the site. One file.
assets/js/site.js                 Navigation, form validation, form submit.
assets/img/                       Photographs, JPEG and WebP pairs
assets/fonts/                     Two self-hosted woff2 files
assets/documents/                 Regulatory PDFs

update-details.py                 Change phone, email or the asset version
sweep.py                          Clicks every control on every page
contrast_audit.py                 Checks every text colour against its real background
```

## Checking your work

Both scripts need Python and Chrome, and a local server running.

```bash
python -m http.server 8123
python sweep.py            # 192 checks: nav, dropdown, burger, forms, console
python contrast_audit.py   # WCAG contrast on every text element
```

`sweep.py` refuses to run if the server is not up, rather than reporting a hollow
pass.

---

## Three things not switched on

Each is a one-line change. All three are explained in `HANDOVER.md`.

1. **The enquiry form has no access key**, so it will not send. Until a key is
   pasted into `contact.html` the form refuses to submit and tells the visitor to
   call, so nothing is ever silently lost.
2. **Document upload is built but disabled** (`data-uploads="off"` on the form).
   Attachments need a paid Web3Forms plan. The Privacy Notice also needs a
   paragraph about uploads before it is turned on.
3. **The review figures on the homepage are unconfirmed** and should be checked
   against the Google Business Profile before the site goes public.
