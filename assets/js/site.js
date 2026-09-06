/* Sikorska Notary — site behaviour
   No dependencies. Progressive enhancement: everything works without JS
   except the mobile menu toggle and the form's conditional fields,
   both of which degrade to "everything visible". */
(function () {
  'use strict';

  /* ---------------- Mobile navigation ---------------- */
  var burger = document.querySelector('.burger');
  var mobileNav = document.getElementById('mobile-nav');

  if (burger && mobileNav) {
    var setNav = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      mobileNav.setAttribute('data-open', String(open));
      document.body.setAttribute('data-nav-open', String(open));
      if (open) {
        var first = mobileNav.querySelector('a, button');
        if (first) first.focus();
      }
    };
    burger.addEventListener('click', function () {
      setNav(burger.getAttribute('aria-expanded') !== 'true');
    });
    mobileNav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNav(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') {
        setNav(false);
        burger.focus();
      }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 940 && burger.getAttribute('aria-expanded') === 'true') setNav(false);
    });
  }

  /* ---------------- Services dropdown ----------------
     Click to open, Escape or an outside click to close. Click rather than hover
     so it behaves identically on a touchpad, a touchscreen and a keyboard. */
  (function () {
    var toggles = document.querySelectorAll('.nav__toggle');
    if (!toggles.length) return;

    function closeAll(except) {
      Array.prototype.forEach.call(toggles, function (t) {
        if (t !== except) t.setAttribute('aria-expanded', 'false');
      });
    }

    Array.prototype.forEach.call(toggles, function (t) {
      t.addEventListener('click', function (e) {
        e.stopPropagation();
        var open = t.getAttribute('aria-expanded') === 'true';
        closeAll(t);
        t.setAttribute('aria-expanded', String(!open));
      });
      /* Down arrow from the toggle drops into the first item */
      t.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          t.setAttribute('aria-expanded', 'true');
          var first = t.nextElementSibling && t.nextElementSibling.querySelector('a');
          if (first) first.focus();
        }
      });
    });

    document.addEventListener('click', function () { closeAll(null); });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      Array.prototype.forEach.call(toggles, function (t) {
        if (t.getAttribute('aria-expanded') === 'true') { t.setAttribute('aria-expanded', 'false'); t.focus(); }
      });
    });
    /* Close when focus leaves the menu entirely */
    document.addEventListener('focusin', function (e) {
      Array.prototype.forEach.call(toggles, function (t) {
        var item = t.closest('.nav__item--has-menu');
        if (item && !item.contains(e.target)) t.setAttribute('aria-expanded', 'false');
      });
    });
  })();

  /* ---------------- Scroll reveal ----------------
     Elements marked .reveal fade and rise as they enter the viewport.
     The hidden state is applied by adding .reveal-ready to <html>, and that
     only happens when we can guarantee we will also reveal them. So with JS
     off, an old browser, or reduced motion, the content is simply visible. */
  (function () {
    var reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !('IntersectionObserver' in window)) return;

    document.documentElement.classList.add('reveal-ready');

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.setAttribute('data-shown', 'true');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    /* Stagger siblings so a grid arrives as a sequence, not a slab.
       Capped so a long list never leaves the last item waiting. */
    var groups = {};
    Array.prototype.forEach.call(reveals, function (el) {
      var key = el.getAttribute('data-reveal-group');
      if (key) {
        groups[key] = (groups[key] || 0) + 1;
        var i = groups[key] - 1;
        if (i > 0) el.style.setProperty('--reveal-delay', Math.min(i * 70, 350) + 'ms');
      }
      io.observe(el);
    });

    /* Anything already in view on load reveals immediately rather than
       waiting for a scroll that may never come on a short page. */
    requestAnimationFrame(function () {
      Array.prototype.forEach.call(reveals, function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) {
          el.setAttribute('data-shown', 'true');
          io.unobserve(el);
        }
      });
    });
  })();

  /* ---------------- Enquiry form ---------------- */
  var form = document.getElementById('enquiry-form');
  if (!form) return;

  /* Conditional blocks: [data-when="fieldName:value1|value2"] */
  var conditionals = Array.prototype.slice.call(form.querySelectorAll('[data-when]'));

  function currentValue(name) {
    var els = form.elements[name];
    if (!els) return '';
    if (els.length && typeof els.length === 'number' && !els.tagName) {
      for (var i = 0; i < els.length; i++) if (els[i].checked) return els[i].value;
      return '';
    }
    return els.value || '';
  }

  function syncConditionals() {
    conditionals.forEach(function (block) {
      var parts = block.getAttribute('data-when').split(':');
      var name = parts[0];
      var wanted = (parts[1] || '').split('|');
      var visible = wanted.indexOf(currentValue(name)) !== -1;
      block.setAttribute('data-visible', String(visible));
      /* Don't validate or submit hidden fields */
      Array.prototype.forEach.call(block.querySelectorAll('input, select, textarea'), function (f) {
        f.disabled = !visible;
      });
    });
  }

  form.addEventListener('change', syncConditionals);
  syncConditionals();

  /* A deadline inside three days should prompt a call, not an inbox wait. */
  var deadlineField = form.elements['deadline'];
  var urgentPrompt = document.getElementById('urgent-prompt');
  if (deadlineField && urgentPrompt) {
    deadlineField.addEventListener('change', function () {
      if (!deadlineField.value) { urgentPrompt.removeAttribute('data-show'); urgentPrompt.textContent = ''; return; }
      var days = (new Date(deadlineField.value) - new Date()) / 86400000;
      if (days <= 3) {
        urgentPrompt.innerHTML = 'That is a tight deadline. Please <a href="tel:+447401388094">call 07401 388 094</a> as well as sending this form, so it is not waiting in an inbox.';
        urgentPrompt.setAttribute('data-show', 'true');
      } else {
        urgentPrompt.removeAttribute('data-show');
        urgentPrompt.textContent = '';
      }
    });
  }

  /* Inline validation with real messages, announced to screen readers */
  function messageFor(field) {
    var v = field.validity;
    var label = field.getAttribute('data-label') || 'This field';
    if (v.valueMissing) {
      if (field.type === 'radio') return 'Please choose an option.';
      if (field.type === 'checkbox') return 'Please tick this box so I can reply to you.';
      if (field.tagName === 'SELECT') return 'Please choose an option.';
      return label + ' is required.';
    }
    if (v.typeMismatch && field.type === 'email') return 'Please enter a valid email address, for example name@company.co.uk';
    if (v.patternMismatch && field.type === 'tel') return 'Please enter a valid UK phone number.';
    if (v.tooShort) return label + ' needs at least ' + field.minLength + ' characters.';
    return 'Please check this field.';
  }

  function showError(field, msg) {
    var wrap = field.closest('.field, .fieldset');
    if (!wrap) return;
    var box = wrap.querySelector('.field__error');
    field.setAttribute('aria-invalid', 'true');
    if (box) {
      box.textContent = msg;
      box.setAttribute('data-show', 'true');
      if (!field.getAttribute('aria-describedby')) field.setAttribute('aria-describedby', box.id);
    }
  }

  function clearError(field) {
    var wrap = field.closest('.field, .fieldset');
    if (!wrap) return;
    var box = wrap.querySelector('.field__error');
    field.removeAttribute('aria-invalid');
    if (box) { box.textContent = ''; box.setAttribute('data-show', 'false'); }
  }

  Array.prototype.forEach.call(form.querySelectorAll('input, select, textarea'), function (field) {
    field.addEventListener('blur', function () {
      if (field.disabled) return;
      if (!field.checkValidity()) showError(field, messageFor(field)); else clearError(field);
    });
    field.addEventListener('input', function () {
      if (field.getAttribute('aria-invalid') === 'true' && field.checkValidity()) clearError(field);
    });
  });

  /* The status element is a SIBLING of the form, not a child, so it has to be
     looked up from the panel. Scoping this to the form meant every error and
     guard message was silently going nowhere. */
  var panelEl = form.closest('.form-panel') || form.parentNode;
  var status = (panelEl && panelEl.querySelector('.form-status')) ||
               document.querySelector('.form-status');


  form.addEventListener('submit', function (e) {
    e.preventDefault();

    /* Safety guard. Until the Web3Forms access key is pasted into contact.html the
       form must never appear to send. Silently losing an enquiry is worse than
       telling the visitor to pick up the phone. */
    var action = form.getAttribute('action');
    var keyField = form.elements['access_key'];
    var hasKey = keyField && keyField.value && keyField.value.trim().length > 10;
    if (!action || action === '#' || !hasKey) {
      if (status) {
        status.setAttribute('data-state', 'error');
        status.innerHTML = 'This form is not able to send enquiries yet. Please call ' +
          '<a href="tel:+447401388094">07401 388 094</a> or email ' +
          '<a href="mailto:office@sikorskanotary.co.uk">office@sikorskanotary.co.uk</a> ' +
          'and your enquiry will reach us directly.';
        status.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }
      return;
    }

    syncConditionals();

    var invalid = null;
    Array.prototype.forEach.call(form.querySelectorAll('input, select, textarea'), function (field) {
      if (field.disabled || field.type === 'hidden') return;
      if (!field.checkValidity()) {
        showError(field, messageFor(field));
        if (!invalid) invalid = field;
      } else {
        clearError(field);
      }
    });


    if (invalid) {
      if (status) {
        status.setAttribute('data-state', 'error');
        status.textContent = 'Please check the highlighted fields and try again.';
      }
      invalid.focus();
      invalid.scrollIntoView({ block: 'center', behavior: 'smooth' });
      return;
    }

    if (status) { status.removeAttribute('data-state'); status.textContent = ''; }

    /* A tight deadline is flagged in the subject line so urgent enquiries are
       visible in the inbox without opening them, and the subject names the
       matter so the inbox can be sorted at a glance. */
    var deadline = form.elements['deadline'];
    var subject = form.elements['subject'];
    if (subject) {
      var urgent = '';
      if (deadline && deadline.value) {
        var days = (new Date(deadline.value) - new Date()) / 86400000;
        if (days <= 3) urgent = '[URGENT] ';
      }
      var who = currentValue('client_type') === 'business' ? 'Business' : 'Individual';
      var what = currentValue('document_type') || 'notarial services';
      var where = currentValue('destination');
      subject.value = urgent + who + ' enquiry: ' + what + (where ? ' (' + where + ')' : '');
    }

    var btn = form.querySelector('button[type="submit"]');
    var btnText = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

    /* Submit over AJAX so the visitor stays on the page and gets a real
       confirmation, rather than being thrown to a third party thank-you page. */
    var data = new FormData(form);
    fetch(form.action, {
      method: 'POST',
      body: data,
      headers: { 'Accept': 'application/json' }
    })
      .then(function (res) { return res.json().then(function (j) { return { ok: res.ok, body: j }; }); })
      .then(function (r) {
        if (!r.ok) throw new Error((r.body && r.body.message) || 'Send failed');
        showSuccess();
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = btnText; }
        if (status) {
          status.setAttribute('data-state', 'error');
          status.innerHTML = 'Sorry, that did not send. Please try again, or call ' +
            '<a href="tel:+447401388094">07401 388 094</a> or email ' +
            '<a href="mailto:office@sikorskanotary.co.uk">office@sikorskanotary.co.uk</a>.';
          status.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
      });
  });

  /* Replace the form with a confirmation that tells the visitor what happens next.
     The old site's form "disappeared into the void"; this is the fix. */
  function showSuccess() {
    var panel = form.closest('.form-panel') || form.parentNode;
    var box = document.createElement('div');
    box.className = 'form-success';
    box.setAttribute('role', 'status');
    box.setAttribute('tabindex', '-1');
    box.innerHTML =
      '<div class="form-success__tick" aria-hidden="true">' +
        '<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20m-1.2 14.2-3.6-3.6 1.4-1.4 2.2 2.2 4.8-4.8 1.4 1.4z"/></svg>' +
      '</div>' +
      '<h2>Thank you, your enquiry has been sent.</h2>' +
      '<p>A confirmation is on its way to the email address you gave. We will come back to you with the next steps, and a fixed fee quote where we can give one.</p>' +
      '<p class="form-note">If your matter is urgent, please call <a href="tel:+447401388094">07401 388 094</a> as well, so it is not waiting in an inbox.</p>';
    panel.innerHTML = '';
    panel.appendChild(box);
    box.focus();
    box.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
})();
