# Sikorska Notary website: handover

Everything needed to put this site live on Hostinger. Written for whoever is doing
the upload, not for whoever built it.

There is no build step, no framework, no database and no dependencies. It is plain
HTML, CSS and one JavaScript file. Whatever you can serve a folder from will serve
this.

---

## What to upload

Upload **everything in this folder** into `public_html`, with one exception: do not
upload the files listed under "Leave these behind" below.

If you are using the Hostinger File Manager, the quickest route is to upload the
zip and use Extract, then delete the zip. FTP works equally well.

**`.htaccess` matters and it is easy to lose.** It starts with a dot, so some file
managers and FTP clients hide it by default. It carries the redirects from the old
site, the 404 page and the caching rules. After uploading, turn on "show hidden
files" and confirm it is actually there.

### Leave these behind

None of these belong on a live server. They are working files.

```
*.md                       (this file, DEPLOY.md, CHANGELOG.md and the rest)
_redirects                 (Netlify format, Apache ignores it, see below)
brand/                     (design exploration, not part of the site)
assets/img/_originals/     (full-size originals of the photographs)
sweep.py
contrast_audit.py
build_brand_pdf.py
Sikorska-Notary-Brand-Diagnostic.pdf
```

`_redirects` and `.htaccess` do the same job for different servers. Hostinger reads
`.htaccess`. Uploading `_redirects` does no harm but it does nothing.

---

## Three things that are not switched on yet

These are deliberate. Each is a one-line change.

### 1. The enquiry form does not send yet

`contact.html` needs a Web3Forms access key. Get one free at
<https://web3forms.com> by entering `office@sikorskanotary.co.uk`; the key arrives
by email. Paste it into the `value=""` of the `access_key` field near the top of
the form.

Until then the form refuses to submit and tells the visitor to call instead, so no
enquiry is ever silently lost. Full instructions, including the auto-reply, are in
`DEPLOY.md`.

### 2. Document upload is built but disabled

The enquiry form has an "Attach the document" field. It is switched off because
**file attachments are a paid Web3Forms feature** (Pro, about $12/month billed
yearly). On the free plan the rest of the form still sends and the file is dropped
silently, which for a notary is the worst possible failure: a client would believe
their passport had arrived when it had not.

To switch it on, once the paid plan is active:

```html
<form id="enquiry-form" ... data-uploads="off" ...>   <!-- change to "on" -->
```

Then send a real test upload and confirm it lands in the inbox before telling
anyone it works.

**Before switching it on, the Privacy Notice needs a paragraph about document
uploads.** Clients will attach passports and ID, which is personal data passing
through a third-party service. That is Patrycja's document to update.

### 3. The review figures need confirming

The homepage shows **5.0 out of 5, across 250+ verified Google and Yell reviews**.
Those came from what Patrycja said rather than from a screen. Check them against
the Google Business Profile before this goes public. If they cannot be confirmed,
delete the two marked lines in `index.html` and the panel becomes a plain link
through to the reviews.

---

## Changing the phone number, email or address

**Do not do this by hand.** There is no template, so the header, footer and calls
to action are copied into every page. The phone number appears in **over 110
places** across three formats: the `tel:` link, the version people read, and the
structured data Google uses. The email appears 37 times. Missing a few leaves a
notary with a wrong number on some pages, which means lost enquiries.

There is a script for it. Run it from inside the website folder:

    python update-details.py                            show what is set, and where
    python update-details.py --phone "07123 456789"     preview the change
    python update-details.py --phone "07123 456789" --apply
    python update-details.py --email new@example.com --apply

Nothing is written without `--apply`. Without it you get a list of what would
change, per file, and no files are touched.

The phone number can be given as `07123 456789` or `+44 7123 456789`. The script
works out the other formats itself.

## The one thing that will bite you later

The stylesheet and script are linked with a version on the end:

```html
<link rel="stylesheet" href="assets/css/site.css?v=20260817">
```

That number is what makes browsers pick up a change. **If you edit `site.css` or
`site.js` and do not change the number, returning visitors keep the old file and
your change appears not to have worked.**

The same script handles it:

    python update-details.py --bump-version --apply

Then re-upload the HTML files as well as the changed asset.

Images do not need this. They are only ever added, not edited in place.

---

## After it is live

1. Visit `https://sikorskanotary.co.uk` with no www and confirm it lands on
   `https://www.sikorskanotary.co.uk` with the padlock.
2. Visit `/apostille-and-legislation.html` (the old misspelled filename) and
   confirm it 301s to the correct page rather than 404ing. That page has rankings
   worth keeping.
3. Visit any nonsense URL and confirm you get the branded 404, not the host's.
4. Send a test enquiry from a phone.
5. Tap the phone number on a phone and confirm it dials.
6. Submit `https://www.sikorskanotary.co.uk/sitemap.xml` in Google Search Console.

`DEPLOY.md` has the longer version of this list, plus how to roll back.

---

## Structure, if you need to change something

```
index.html                        Home
notarial-service.html             Notarial services
apostille-and-legalisation.html   Apostille & legalisation
will-writing-service.html         Will writing
for-business.html                 For business
fees-and-disbursements.html       Fees
practice.html                     The Practice, biography and portrait
contact.html                      Contact and the enquiry form
polski.html                       Polish language page
legal-and-regulatory.html         Regulatory, complaints, documents
404.html                          Not found

assets/css/site.css               Every style on the site. One file.
assets/js/site.js                 Nav, form validation, form submit. One file.
assets/img/                       Photographs, as JPEG and WebP pairs
assets/fonts/                     Two self-hosted woff2 files
assets/documents/                 Regulatory PDFs
```

The header, footer and navigation are copied into each page rather than included,
because there is no build step. **If you change the navigation or the footer, change
it in all eleven files.**

### Two things not to rewrite

- **The Polish page** is Patrycja's own writing, not a translation. Do not machine
  translate or edit it without asking her.
- **Her biography** on `practice.html` is her own words, supplied verbatim.

---

## Checking your work

Two scripts in this folder check the site. Both need Python and Chrome, and both
run against a local copy:

```
python -m http.server 8123
python contrast_audit.py     # every text colour against its real background
python sweep.py              # clicks every control on every page, desktop and mobile
```

`sweep.py` runs 192 checks. If you change anything structural, run it.
