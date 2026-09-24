// TaskForge client: talks to the JSON API with fetch(), no reloads.
(() => {
  const $ = (id) => document.getElementById(id);
  const list = $('list'), state = $('state'), count = $('count');
  let tasks = [], filter = 'all';

  // ---- helpers ----
  function toast(msg, isError = false) {
    const el = document.createElement('div');
    el.className = 'toast' + (isError ? ' error' : '');
    el.textContent = msg;
    $('toasts').appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  async function api(method, path, body) {
    const opts = { method, headers: {} };
    if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    const res = await fetch('/api/tasks' + path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Request failed (' + res.status + ')');
    }
    return res.status === 204 ? null : res.json();
  }

  // ---- rendering ----
  function render() {
    const remaining = tasks.filter((t) => !t.done).length;
    count.textContent = remaining + (remaining === 1 ? ' task' : ' tasks') + ' remaining';
    const shown = tasks.filter((t) => filter === 'all' || (filter === 'done') === t.done);

    list.replaceChildren(...shown.map(itemEl));
    list.setAttribute('aria-busy', 'false');
    state.hidden = shown.length > 0;
    state.textContent = tasks.length === 0 ? 'No tasks yet. Add your first one above ✨'
      : 'Nothing in this view.';
  }

  function itemEl(t) {
    const li = document.createElement('li');
    li.className = 'item' + (t.done ? ' done' : '');
    li.dataset.id = t.id;

    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.checked = t.done; cb.id = 'task-' + t.id;
    // The API can only mark tasks done (no undo), so completed boxes are locked.
    cb.disabled = t.done;
    cb.addEventListener('change', () => complete(t.id));

    const label = document.createElement('label');
    label.className = 'title'; label.htmlFor = cb.id; label.textContent = t.title;

    const del = document.createElement('button');
    del.type = 'button'; del.className = 'btn del'; del.textContent = 'Delete';
    del.setAttribute('aria-label', 'Delete task: ' + t.title);
    del.addEventListener('click', () => remove(t.id, li));

    li.append(cb, label, del);
    return li;
  }

  // ---- actions ----
  async function load() {
    try { tasks = await api('GET', ''); render(); }
    catch (e) { state.hidden = false; state.textContent = 'Could not load tasks.'; toast(e.message, true); }
  }

  async function complete(id) {
    try {
      const updated = await api('PATCH', '/' + id);
      tasks = tasks.map((t) => (t.id === id ? updated : t));
      render(); toast('Task completed');
    } catch (e) { toast(e.message, true); load(); }
  }

  async function remove(id, li) {
    try {
      await api('DELETE', '/' + id);
      li.classList.add('removing');
      setTimeout(() => { tasks = tasks.filter((t) => t.id !== id); render(); }, 200);
      toast('Task deleted');
    } catch (e) { toast(e.message, true); load(); }
  }

  $('add-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = $('title'), btn = e.target.querySelector('button');
    const title = input.value.trim();
    if (!title) return;
    btn.disabled = true;
    try {
      tasks.push(await api('POST', '', { title }));
      input.value = ''; render(); toast('Task added');
    } catch (err) { toast(err.message, true); }
    btn.disabled = false; input.focus();
  });

  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
    filter = tab.dataset.filter;
    document.querySelectorAll('.tab').forEach((x) => x.setAttribute('aria-selected', String(x === tab)));
    render();
  }));

  // ---- theme toggle (overrides prefers-color-scheme, remembered) ----
  $('theme').addEventListener('click', () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (e) { /* ignore */ }
  });

  load();
})();
