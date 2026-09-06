# Deploying

Static HTML. No build step, no Node, no dependencies. Upload the folder and it works.

## Turning the enquiry form on

The form is **fully built and wired**. It needs one value pasting in, and nothing else.

### Step 1: get the access key (about two minutes, free)

1. Go to **https://web3forms.com**
2. Type **office@sikorskanotary.co.uk** into the box on the homepage and press **Create Access Key**
3. A key arrives at that address. It looks like `a1b2c3d4-e5f6-...`

No account, no password, no card. The key simply tells the service which inbox to deliver to.

### Step 2: paste it in

In `contact.html`, find this line near the top of the form:

```html
<input type="hidden" name="access_key" value="">
```

Put the key between the quotes. That is the whole job. The form is now live.

### Step 3: turn on the auto-reply

This is the bit that matters. The original site's form gave no confirmation at all, and an
enquirer with a deadline was left wondering whether it sent. In the Web3Forms dashboard, turn on
**Auto Respond** and paste this in:

> Subject: We have your enquiry, Sikorska Notary
>
> Thank you for contacting Sikorska Notary.
>
> We have your enquiry and will come back to you with the next steps, and a fixed fee quote
> where we can give one.
>
> If your matter is urgent, please call 07401 388 094 so it is not waiting in an inbox.
>
> Sikorska Notary Limited
> Notarial services for England and Wales
> 07401 388 094 · office@sikorskanotary.co.uk

### What already works, with no further setup

- Submits without leaving the page, and shows a proper confirmation
- **Refuses to submit while the key is empty**, and tells the visitor to call instead, so an
  enquiry can never be silently lost
- Spam honeypot
- Subject lines are built for triage: `[URGENT] Business enquiry: Corporate power of attorney (Poland)`
- A deadline within three days prompts the visitor to call as well as sending

### Testing it

Send yourself one enquiry as an individual and one as a business. Check the subject line
formats correctly, the auto-reply arrives, and the reply-to address is the enquirer's.

---

## Before you upload

Three other things must be done or the site will look unfinished:

1. **Remove the build notes.** Search the project for `placeholder-note`. Every match is a
   dashed box that must not go live. Each one names a decision Patrycja has to make first.
2. **Add analytics.** There is a marked slot in the `<head>` of `index.html`. Without it, every
   future decision about this site is a guess.
3. **Delete the `brand/` folder and the `.md` files.** They are internal working documents,
   not part of the website. `brand/index.html` is set to `noindex` and is unlinked, but it should
   not be sitting on a live server regardless.

## Host options

**Netlify or Cloudflare Pages.** Drag the folder in. `_redirects` is read automatically by
Netlify. Cloudflare Pages reads `_redirects` too. Free tier is ample for a brochure site.

**Existing host.** The current site appears to be on shared hosting serving pre-built static
files, so replacing the files in place should work. Keep a copy of the old build first.

## Redirects

`_redirects` is Netlify format. If the host uses Apache, use this `.htaccess` instead:

```apache
RewriteEngine On

# Force https + www
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} !^www\. [NC]
RewriteRule ^(.*)$ https://www.sikorskanotary.co.uk/$1 [R=301,L]

# Renamed page: the old filename said "legislation", the page is about legalisation
RewriteRule ^apostille-and-legislation\.html$ /apostille-and-legalisation.html [R=301,L]

# Pages the old homepage linked to but never shipped
RewriteRule ^individual-client\.html$ /notarial-service.html#individual [R=301,L]
RewriteRule ^corporate-client\.html$  /for-business.html [R=301,L]

ErrorDocument 404 /404.html
```

If the host is IIS, the same rules go in `web.config` as `<rewrite><rules>`.

## After you upload

1. **Submit the sitemap** at https://www.sikorskanotary.co.uk/sitemap.xml to Google Search
   Console. Verify the property if it is not already.
2. **Test the redirects.** Visit `/apostille-and-legislation.html` and confirm it lands on the
   new page with a 301, not a 404. That page has existing rankings to preserve.
3. **Send yourself a test enquiry** through the form, on a phone, and confirm both the email
   and the auto-reply arrive.
4. **Check the phone link** by tapping it on an actual phone.
5. **Claim the Google Business Profile** if it is not already, with the address, hours and
   phone matching the footer exactly. Character for character. Inconsistent details suppress
   local pack ranking.

## Rolling back

Nothing here depends on the old site, so rolling back is just restoring the previous files.
Keep the old build until the new one has run for a fortnight.
