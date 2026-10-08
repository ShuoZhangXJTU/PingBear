const { Plugin, Modal, Notice, TFile } = require('obsidian');

// arXiv ids look like 2609.28654; 小红书 notes are stored as xhs-<note id>.
const valid = (date, id) => /^\d{4}-\d{2}-\d{2}$/.test(date || '')
  && (/^\d{4}\.\d{4,5}$/.test(id || '') || /^xhs-[0-9a-f]{16,32}$/.test(id || '')
    || /^xhs-[0-9a-f]{16,32}-\d{1,3}$/.test(id || '')
    || /^link-[0-9a-f]{6,32}$/.test(id || '') || /^blog-[0-9a-f]{6,32}$/.test(id || ''));
const safe = text => String(text || '').replace(/[\\/:*?"<>|\n\r\t]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 90);
const entryPath = record => `论文/${safe((record.tags || [])[0] || '其他')}/${safe(record.title || record.id)}.md`;
const sleep = ms => new Promise(resolve => window.setTimeout(resolve, ms));
let Platform = { isDesktopApp: true };
try { Platform = require('obsidian').Platform || Platform; } catch (e) { /* 移动端兜底 */ }

class AskModal extends Modal {
  constructor(plugin, id) { super(plugin.app); Object.assign(this, {plugin, id}); }
  onOpen() {
    this.contentEl.createEl('h3', {text: `提问 · ${this.id}`});
    this.status = this.contentEl.createEl('div', {cls: 'research-archive-ask-status',
      text: '问题会带着这篇论文的正文（或截图文字）去问，回答和“沉淀”会写进 问答/ 目录，已归档的还会追加到笔记。'});
    this.input = this.contentEl.createEl('textarea',
      {placeholder: '想问什么？例如：它的 harness 具体怎么设计的？训练数据是怎么造的？', cls: 'research-archive-note'});
    this.input.rows = 3;
    const row = this.contentEl.createDiv({cls: 'research-archive-controls'});
    this.send = row.createEl('button', {text: '提问', cls: 'mod-cta'});
    const history = row.createEl('button', {text: '查看问答记录'});
    this.answerEl = this.contentEl.createDiv({cls: 'research-archive-answer'});
    this.send.onclick = () => this.askNow();
    this.input.addEventListener('keydown', event => {
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) this.askNow();
    });
    history.onclick = async () => {
      const file = this.app.vault.getAbstractFileByPath(`问答/${this.id}.md`);
      if (file) await this.app.workspace.getLeaf(false).openFile(file);
      else new Notice('这个条目还没有问答记录');
    };
    this.input.focus();
  }
  onClose() { this.contentEl.empty(); }
  async askNow() {
    const question = this.input.value.trim();
    if (!question) return;
    this.send.disabled = true;
    this.answerEl.empty();
    this.status.setText('正在读论文正文并回答，大约 20–60 秒…');
    const started = Date.now();
    this.plugin.runKnowledge(['ask', '--id', this.id, '--question', question]);
    const path = `.research/knowledge/answers/${this.id}.json`;
    for (let attempt = 0; attempt < 200; attempt++) {
      await sleep(1500);
      try {
        const data = JSON.parse(await this.app.vault.adapter.read(path));
        if (data.question === question && Date.parse(data.at) > started - 3000) {
          this.status.setText(`依据：${data.confidence}　·　沉淀：${data.point}`);
          const { MarkdownRenderer } = require('obsidian');
          await MarkdownRenderer.render(this.app, data.answer, this.answerEl, '', this);
          this.send.disabled = false;
          this.input.value = '';
          return;
        }
      } catch (error) { /* 还没写好就继续等 */ }
    }
    this.status.setText('等太久没拿到回答。可以点「查看问答记录」看是否已经写入，或再问一次。');
    this.send.disabled = false;
  }
}

class LibraryModal extends Modal {
  constructor(plugin) { super(plugin.app); this.plugin = plugin; }
  onOpen() {
    this.contentEl.createEl('h3', {text: '归档问答'});
    this.status = this.contentEl.createEl('div', {cls: 'research-archive-ask-status',
      text: '在已归档论文（含深读 takeaway、你自己的问答沉淀）和专题体系页里检索。「搜索」秒回只列命中，「提问」会带上最相关的几篇让模型带引用回答。'});
    this.input = this.contentEl.createEl('textarea',
      {placeholder: '例如：harness 的改进主要落在哪几个地方？／ 哪些工作在讲同一件事的不同侧面？', cls: 'research-archive-note'});
    this.input.rows = 3;
    const row = this.contentEl.createDiv({cls: 'research-archive-controls'});
    this.searchButton = row.createEl('button', {text: '搜索', cls: 'mod-cta'});
    this.askButton = row.createEl('button', {text: '提问', cls: 'mod-cta'});
    const log = row.createEl('button', {text: '对话记录'});
    this.answerEl = this.contentEl.createDiv({cls: 'research-archive-answer'});
    this.searchButton.onclick = () => this.run('search');
    this.askButton.onclick = () => this.run('ask');
    this.input.addEventListener('keydown', event => {
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) this.run('ask');
    });
    log.onclick = async () => {
      const file = this.app.vault.getAbstractFileByPath('问答/知识助手.md');
      if (file) await this.app.workspace.getLeaf(false).openFile(file);
      else new Notice('还没有对话记录');
    };
    this.input.focus();
  }
  onClose() { this.contentEl.empty(); }
  async run(kind) {
    const query = this.input.value.trim();
    if (!query) return;
    this.searchButton.disabled = this.askButton.disabled = true;
    this.answerEl.empty();
    this.status.setText(kind === 'search' ? '正在检索归档…' : '正在检索归档并让模型带引用回答，大约 20–60 秒…');
    const started = Date.now();
    const path = kind === 'search' ? '.research/knowledge/answers/archive-search.json'
      : '.research/knowledge/answers/archive.json';
    this.plugin.runScript('scripts/library.py', [kind === 'search' ? 'search' : 'ask',
      kind === 'search' ? '--query' : '--question', query]);
    for (let attempt = 0; attempt < 200; attempt++) {
      await sleep(1500);
      try {
        const data = JSON.parse(await this.app.vault.adapter.read(path));
        const match = kind === 'search' ? data.query === query : data.question === query;
        if (!match || Date.parse(data.at) < started - 3000) continue;
        const { MarkdownRenderer } = require('obsidian');
        if (kind === 'search') {
          if (!data.hits.length) { this.answerEl.setText('没有命中，换个关键词试试。'); }
          else {
            const markdown = data.hits.map(hit => `- [[${hit.path.replace(/\.md$/, '')}|${hit.title}]]　<sub>${hit.score}</sub>`).join('\n');
            await MarkdownRenderer.render(this.app, markdown, this.answerEl, '', this);
          }
          this.status.setText(`命中 ${data.hits.length} 条`);
        } else {
          await MarkdownRenderer.render(this.app, data.answer, this.answerEl, '', this);
          this.status.setText(data.gaps ? `缺口：${data.gaps}` : '已依据归档回答，来源见文中链接');
        }
        this.searchButton.disabled = this.askButton.disabled = false;
        return;
      } catch (error) { /* 还没写完，继续等 */ }
    }
    this.status.setText('等太久没拿到结果，可以点「对话记录」查看是否已经写入。');
    this.searchButton.disabled = this.askButton.disabled = false;
  }
}

// 灵感速记：一个输入框，Cmd+Enter 保存，写完自动按主题归档
class IdeaModal extends Modal {
  constructor(plugin) { super(plugin.app); this.plugin = plugin; }
  onOpen() {
    this.contentEl.createEl('h3', {text: '记一条灵感'});
    this.contentEl.createEl('div', {cls: 'research-archive-ask-status',
      text: '一句话就行，回车（Cmd+Enter）保存。存进 灵感/收件箱，每天早报跑完自动按主题归到 灵感/<主题>.md。'});
    this.input = this.contentEl.createEl('textarea', {placeholder: '例如：记忆模块能不能也只写一个面，让验证器来判', cls: 'research-archive-note'});
    this.input.rows = 3;
    const row = this.contentEl.createDiv({cls: 'research-archive-controls'});
    this.save = row.createEl('button', {text: '保存', cls: 'mod-cta'});
    const open = row.createEl('button', {text: '打开收件箱'});
    this.save.onclick = () => this.submit();
    this.input.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) this.submit(); });
    open.onclick = async () => {
      const file = this.app.vault.getAbstractFileByPath('灵感/收件箱.md');
      if (file) await this.app.workspace.getLeaf(false).openFile(file);
    };
    this.input.focus();
  }
  onClose() { this.contentEl.empty(); }
  async submit() {
    const text = this.input.value.trim();
    if (!text) return;
    try {
      const base = this.app.vault.adapter.getBasePath();
      const { execFileSync } = require('child_process');
      execFileSync('/usr/bin/python3', [`${base}/scripts/ideas.py`, 'add', '--text', text], {cwd: base, timeout: 20000});
      new Notice('已记下 ✅（早报后会按主题归档）');
      this.close();
    } catch (error) {
      new Notice('记录失败：' + error.message);
    }
  }
}

class NoteModal extends Modal {
  constructor(plugin, date, id) { super(plugin.app); Object.assign(this, {plugin, date, id}); }
  onOpen() {
    this.contentEl.createEl('h3', {text: '归档论文'});
    const input = this.contentEl.createEl('textarea', {placeholder: '想记住什么？补一两句即可，也可以留空。', cls: 'research-archive-note'});
    input.rows = 3;
    const button = this.contentEl.createEl('button', {text: '保存归档', cls: 'mod-cta'});
    button.onclick = async () => {
      button.disabled = true;
      try { await this.plugin.archive(this.date, this.id, input.value); this.close(); }
      catch (e) { new Notice(`归档失败：${e.message}`); button.disabled = false; }
    };
    input.focus();
  }
  onClose() { this.contentEl.empty(); }
}

module.exports = class ResearchArchive extends Plugin {
  async onload() {
    this.pending = new Map();
    this.controls = new Set();
    // Load marker so the daily pipeline can confirm the plugin really loaded.
    this.app.vault.adapter.write('.research/plugin-loaded.json',
      JSON.stringify({ loaded_at: new Date().toISOString(), version: this.manifest.version }, null, 2) + '\n').catch(() => {});
    this.registerMarkdownPostProcessor(el => {
      // 诊断：Obsidian 是否还把 obsidian:// 链接渲染成 <a>（写进 .research/plugin-diag.json）
      try {
        const all = el.querySelectorAll('a').length;
        const matched = el.querySelectorAll('a[href^="obsidian://research-archive?"]').length;
        const raw = (el.textContent || '').includes('obsidian://research-archive');
        if (all || raw) {
          this.diag = this.diag || { blocks: 0, anchors: 0, matched: 0, textOnly: 0 };
          this.diag.blocks += 1; this.diag.anchors += all; this.diag.matched += matched;
          if (raw && !matched) this.diag.textOnly += 1;
          if (!this.diagWritten) {
            this.diagWritten = true;
            this.diagAt = Date.now();
            this.app.vault.adapter.write('.research/plugin-diag.json',
              JSON.stringify(this.diag, null, 2) + '\n').catch(() => {});
          }
        }
      } catch (e) { /* 诊断不影响正常渲染 */ }
      for (const anchor of el.querySelectorAll('a[href^="obsidian://research-archive?"]')) {
        try {
        const url = new URL(anchor.getAttribute('href'));
        const date = url.searchParams.get('date'), id = url.searchParams.get('id');
        if (!valid(date,id)) continue;
        const box = document.createElement('span');
        box.className = 'research-archive-controls';
        const archive = box.createEl('button', {text: '归档', cls: 'research-archive-save'});
        const note = box.createEl('button', {text: '加备注', cls: 'research-archive-add'});
        const ask = box.createEl('button', {text: '提问', cls: 'research-archive-ask'});
        const input = box.createEl('textarea', {placeholder: '补一两句，随论文一起保存…', cls: 'research-archive-note'});
        input.rows = 2; input.hidden = true;
        const control = {box, archive, note, input, id};
        this.controls.add(control);
        const update = () => {
          let saved = false;
          try { saved = !!this.findArchived(id); } catch (e) { saved = false; }
          archive.textContent = saved ? '已归档 · 打开' : '归档';
          note.textContent = saved ? '补充备注' : '加备注';
        };
        control.update = update; update();
        note.onclick = () => {
          if (this.findArchived(id)) {
            new NoteModal(this,date,id).open();
          } else { input.hidden = !input.hidden; if (!input.hidden) input.focus(); }
        };
        ask.onclick = () => new AskModal(this, id).open();
        archive.onclick = async () => {
          archive.disabled = true;
          try {
            const existing = this.findArchived(id);
            if (existing && !input.value.trim()) await this.app.workspace.getLeaf(false).openFile(existing);
            else { await this.archive(date,id,input.value); input.value = ''; input.hidden = true; }
            this.refresh();
          } catch (e) { new Notice(`归档失败：${e.message}`); }
          finally { archive.disabled = false; }
        };
        anchor.replaceWith(box);
        } catch (error) {
          // 单个条目出错不能拖垮整篇的按钮渲染
          console.error('research-archive: 条目按钮渲染失败', error);
        }
      }
    });
    this.registerObsidianProtocolHandler('research-archive', ({date,id}) => {
      if (valid(date,id)) new NoteModal(this,date,id).open();
    });
    this.addCommand({id: 'rebuild-tag-index', name: '重建标签索引',
      callback: async () => { await this.rebuildIndex(); new Notice('标签索引已重建'); }});
    this.addCommand({id: 'rebuild-catalog', name: '重建历史目录',
      callback: () => { this.runScript('scripts/catalog.py', []); new Notice('正在重建 索引/目录'); }});
    this.addCommand({id: 'rebuild-knowledge', name: '重建主题知识体系',
      callback: () => this.runScript('scripts/knowledge.py', ['rebuild'])});
    this.addCommand({id: 'process-inbox', name: '读取我的链接',
      callback: () => { this.runScript('scripts/inbox.py', ['process']); new Notice('开始处理收件箱里的链接，稍后看今日简报的「我的链接」段落'); }});
    this.addCommand({id: 'refresh-archive-state', name: '刷新归档状态',
      callback: () => { this.archiveMap = null; this.refresh(); new Notice('归档状态已刷新'); }});
    this.addCommand({id: 'sync-cloud', name: '同步到云盘（手机阅读）',
      callback: () => { this.runScript('scripts/sync_cloud.py', ['both']); new Notice('正在同步到云盘…'); }});
    this.addCommand({id: 'library-ask', name: '归档问答', callback: () => new LibraryModal(this).open()});
    this.addCommand({id: 'capture-idea', name: '记一条灵感', callback: () => new IdeaModal(this).open()});
    this.addRibbonIcon('pencil', '记一条灵感', () => new IdeaModal(this).open());
    this.registerEvent(this.app.workspace.on('file-open', () => this.attachToc()));
    this.registerEvent(this.app.workspace.on('active-leaf-change', () => this.attachToc()));
    this.registerEvent(this.app.vault.on('modify', file => {
      if (/(今日简报|日报)/.test(file?.basename || '')) this.attachToc();
    }));
    this.addRibbonIcon('message-circle-question', '归档问答', () => new LibraryModal(this).open());
    this.registerEvent(this.app.vault.on('create', () => this.refresh()));
    this.registerEvent(this.app.vault.on('delete', () => this.refresh()));
    this.registerInterval(window.setInterval(() => this.refresh(), 30000));
  }
  refresh() {
    this.archiveMap = null;
    for (const c of this.controls) {
      if (!c.box.isConnected) this.controls.delete(c);
      else c.update();
    }
  }
  // 归档笔记现在按「主题/论文名」存放，用 frontmatter 里的 entry_id 反查。
  findArchived(id) {
    if (!this.archiveMap) {
      this.archiveMap = new Map();
      for (const file of this.app.vault.getMarkdownFiles()) {
        const fm = this.app.metadataCache.getFileCache(file)?.frontmatter;
        if (!fm) continue;
        for (const key of [fm.entry_id, fm.arxiv]) {
          if (key) this.archiveMap.set(String(key).trim(), file);
        }
        if (fm.title) this.archiveMap.set('t:' + String(fm.title).trim().toLowerCase().slice(0, 60), file);
      }
    }
    return this.archiveMap.get(String(id)) || null;
  }
  findArchivedByTitle(title) {
    if (!this.archiveMap) this.findArchived('');
    return this.archiveMap.get('t:' + String(title || '').trim().toLowerCase().slice(0, 60)) || null;
  }
  // 今日简报/日报 左侧悬浮目录：直接读源文件的所有标题（不受阅读视图按需渲染影响）
  async attachToc() {
    try {
      const { MarkdownView } = require('obsidian');
      const view = this.app.workspace.getActiveViewOfType(MarkdownView);
      if (!view?.file || !/(今日简报|日报)/.test(view.file.basename)) return;
      const container = view.contentEl;
      if (!container) return;
      const text = await this.app.vault.cachedRead(view.file);
      const lines = text.split('\n');
      const headings = [];
      lines.forEach((line, index) => {
        const match = /^(#{1,3})\s+(.+)$/.exec(line.trim());
        if (match) headings.push({level: match[1].length, line: index,
          text: match[2].replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/[*`]/g, '').trim()});
      });
      container.querySelectorAll('.research-toc').forEach(el => el.remove());
      if (headings.length < 3) return;
      const box = container.createDiv({cls: 'research-toc'});
      box.createDiv({cls: 'research-toc-title', text: `目录（${headings.length}）`});
      for (const heading of headings) {
        const item = box.createEl('a', {cls: `research-toc-item research-toc-h${heading.level}`,
          text: heading.text.slice(0, 44)});
        item.onclick = event => {
          event.preventDefault();
          const rendered = Array.from(container.querySelectorAll(
            '.markdown-preview-view h1, .markdown-preview-view h2, .markdown-preview-view h3'))
            .find(el => (el.textContent || '').trim().startsWith(heading.text.slice(0, 20)));
          if (rendered) { rendered.scrollIntoView({behavior: 'smooth', block: 'start'}); return; }
          const scroller = container.querySelector('.markdown-preview-view') || container;
          scroller.scrollTop = (heading.line / Math.max(lines.length, 1)) * scroller.scrollHeight;
        };
      }
    } catch (error) { console.error('research-archive: 目录生成失败', error); }
  }
  parseFrontmatter(text) {
    const out = {};
    if (!text.startsWith('---\n')) return out;
    const end = text.indexOf('\n---', 3);
    if (end < 0) return out;
    let key = null;
    for (const line of text.slice(4, end).split('\n')) {
      if (!line.trim()) continue;
      const bullet = line.match(/^\s+-\s+(.*)$/);
      if (bullet && key) { (out[key] = out[key] || []).push(bullet[1].trim().replace(/^"|"$/g, '')); continue; }
      const cut = line.indexOf(':');
      if (cut < 0) continue;
      key = line.slice(0, cut).trim();
      const value = line.slice(cut + 1).trim();
      if (!value) { out[key] = []; continue; }
      if (value.startsWith('[')) {
        try { out[key] = JSON.parse(value); continue; } catch (e) { /* fall through */ }
      }
      out[key] = value.replace(/^"|"$/g, '');
    }
    return out;
  }
  async rebuildIndex() {
    const folder = this.app.vault.getAbstractFileByPath('论文');
    const entries = [];
    for (const child of (folder && folder.children) || []) {
      if (!(child instanceof TFile) || child.extension !== 'md') continue;
      const fm = this.parseFrontmatter(await this.app.vault.cachedRead(child));
      const tags = Array.isArray(fm.tags) ? fm.tags : (fm.tags ? [fm.tags] : []);
      entries.push({id: child.basename, title: fm.title || child.basename, date: fm.selected_from || '',
        summary: fm.summary || '', tags: tags.filter(t => typeof t === 'string' && t.trim())});
    }
    const grouped = new Map();
    for (const entry of entries) for (const tag of entry.tags) {
      if (!grouped.has(tag)) grouped.set(tag, []);
      grouped.get(tag).push(entry);
    }
    const lines = ['# 标签索引', '', '自动生成，改动会被覆盖：归档后由「归档」按钮或 '
      + '`python3 scripts/research.py index --date <日期>` 刷新。', '',
      `已归档 ${entries.length} 篇，覆盖 ${grouped.size} 个标签。`, ''];
    if (!entries.length) lines.push('还没有归档的论文。');
    const ordered = [...grouped.entries()].sort((a, b) => b[1].length - a[1].length || (a[0] < b[0] ? -1 : 1));
    for (const [tag, items] of ordered) {
      lines.push(`## ${tag}（${items.length}）`, '');
      for (const item of items.slice().sort((a, b) => (a.date < b.date ? 1 : -1))) {
        const tail = [item.date, item.summary].filter(Boolean).join(' · ');
        lines.push(`- [[论文/${item.id}|${item.title}]]` + (tail ? ` — ${tail}` : ''));
      }
      lines.push('');
    }
    const untagged = entries.filter(e => !e.tags.length);
    if (untagged.length) {
      lines.push('## 未打标签', '');
      for (const e of untagged) lines.push(`- [[论文/${e.id}|${e.title}]]`);
      lines.push('');
    }
    const body = lines.join('\n').replace(/\n+$/, '') + '\n';
    if (!this.app.vault.getAbstractFileByPath('索引')) await this.app.vault.createFolder('索引');
    const existing = this.app.vault.getAbstractFileByPath('索引/标签.md');
    if (existing) await this.app.vault.modify(existing, body);
    else await this.app.vault.create('索引/标签.md', body);
  }
  // 在后台跑本地脚本（归档深读、体系重建、读收件箱链接）。
  runScript(script, args) {
    const action = this.inferAction([script, ...(args || [])]);
    if (!Platform?.isDesktopApp) return this.queueRequest({action, ...this.inferPayload(args)});
    try {
      const { execFile } = require('child_process');
      const base = this.app.vault.adapter.getBasePath();
      const child = execFile('/usr/bin/python3', [`${base}/${script}`, ...args],
        { cwd: base, detached: true });
      child.unref();
      child.on('error', error => new Notice('知识体系任务没启动：' + error.message));
    } catch (error) {
      new Notice('知识体系任务没启动：' + error.message);
    }
  }
  inferPayload(args) {
    const list = args || [];
    const text = list.find(item => typeof item === 'string' && item && !item.startsWith('--')) || '';
    const idIndex = list.indexOf('--id');
    const questionIndex = list.indexOf('--question');
    const queryIndex = list.indexOf('--query');
    return {
      id: idIndex >= 0 ? list[idIndex + 1] : text,
      question: questionIndex >= 0 ? list[questionIndex + 1] : text,
      text: queryIndex >= 0 ? list[queryIndex + 1] : text,
      mode: list.includes('search') ? 'search' : 'ask',
    };
  }
  // 手机端：把动作写进 .research/requests/，Mac 端 scripts/requests.py 会执行
  async queueRequest(payload) {
    try {
      const dir = '.research/requests';
      if (!(await this.app.vault.adapter.exists(dir))) await this.app.vault.adapter.mkdir(dir);
      const name = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;
      const body = {
        action: payload.action === 'run' ? this.inferAction(payload.args) : payload.action,
        ...payload,
        queued_at: new Date().toISOString(),
        device: 'mobile',
      };
      await this.app.vault.adapter.write(`${dir}/${name}`, JSON.stringify(body, null, 2));
      new Notice('已发给电脑执行，稍后同步回结果（需 Mac 开机）');
      return name;
    } catch (error) {
      new Notice('排队失败：' + error.message);
    }
  }
  inferAction(args) {
    const joined = (args || []).join(' ');
    if (joined.includes('knowledge.py')) {
      if (joined.includes(' ask')) return 'ask';
      if (joined.includes(' deepen')) return 'deepen';
      return 'rebuild';
    }
    if (joined.includes('library.py')) return 'library';
    if (joined.includes('inbox.py')) return 'process-inbox';
    if (joined.includes('ideas.py')) return 'idea';
    if (joined.includes('catalog.py')) return 'catalog';
    return 'unknown';
  }
  runKnowledge(args) { this.runScript('scripts/knowledge.py', args); }
  async archive(date,id,note='') {
    if (!valid(date,id)) throw new Error('论文编号无效');
    if (this.pending.has(id)) return this.pending.get(id);
    const work = this.savePaper(date,id,note);
    this.pending.set(id,work);
    try { return await work; } finally { this.pending.delete(id); }
  }
  async savePaper(date,id,note) {
    let filePath = null;
    let existing = this.findArchived(id);
    if (existing) {
      if (!(existing instanceof TFile)) throw new Error('归档路径不是文件');
      if (note.trim()) {
        await this.app.vault.process(existing, text => `${text.trimEnd()}\n\n## 补充备注\n\n${note.trim()}\n`);
        new Notice('备注已补充');
      } else new Notice('这篇已归档');
      this.refresh(); return existing;
    }
    // A paper found in 小红书 is archived under its arXiv id, so both digests are searched.
    let p = null;
    for (const digest of [`.research/digests/${date}.json`, `.research/xhs/digests/${date}.json`,
        `.research/inbox/digests/${date}.json`, `.research/blogs/digests/${date}.json`]) {
      try {
        const manifest = JSON.parse(await this.app.vault.adapter.read(digest));
        p = (manifest.papers || []).find(entry => entry.id === id);
      } catch (e) { p = null; }
      if (p) break;
    }
    if (!p) throw new Error('该日报中没有这条内容');
    const tags = (p.tags || p.topics || []).filter(t => typeof t === 'string' && /^[\p{L}\p{N}_-]+$/u.test(t));
    const isArxiv = /^\d{4}\.\d{4,5}$/.test(id);
    const link = p.url || (isArxiv ? `https://arxiv.org/abs/${id}` : '');
    const pdf = p.pdf || (isArxiv ? `https://arxiv.org/pdf/${id}` : '');
    let extra = '';
    if (isArxiv) extra += `\n[PDF](${pdf})\n`;
    if (p.note_url) extra += `\n[小红书原帖](${p.note_url})\n`;
    if (p.images && p.images.length) {
      extra += '\n## 截图\n\n' + p.images.map((img, i) => `![图 ${i + 1}](${img.url})`).join('\n\n') + '\n';
    }
    if (p.ocr) extra += '\n## 截图文字（OCR）\n\n' + String(p.ocr).slice(0, 20000) + '\n';
    const identity = isArxiv ? `arxiv: "${id}"` : `source: xiaohongshu\nnote_url: ${JSON.stringify(p.note_url || '')}`;
    if (!filePath) filePath = entryPath(p);
    const front = ['---', `entry_id: "${id}"`, identity, `title: ${JSON.stringify(p.title)}`,
      `summary: ${JSON.stringify(p.summary || '')}`, `selected_from: ${date}`, 'status: to-read',
      `primary_tag: ${tags[0] || '其他'}`, 'tags:'].concat(tags.map(t => `  - ${t}`), ['---']);
    const heading = link ? `[${p.title}](${link})` : p.title;
    const from = p.source === 'xiaohongshu'
      ? `来源：[[日报/${date}-小红书]]，X${p.number}（tabris 的笔记）。`
      : `来源：[[日报/${date}]]，第 ${p.number} 篇。`;
    const contents = front.join('\n') + `\n\n# ${heading}\n\n${p.summary}\n\n${tags.map(t=>'#'+t).join(' ')}\n${extra}\n${from}\n\n## 我的备注\n\n${note.trim()}\n`;
    if (!this.app.vault.getAbstractFileByPath('论文')) await this.app.vault.createFolder('论文');
    const folder = filePath.split('/').slice(0, -1).join('/');
    if (folder && !this.app.vault.getAbstractFileByPath(folder)) await this.app.vault.createFolder(folder);
    const file = await this.app.vault.create(filePath,contents);
    await this.rebuildIndex();
    this.runKnowledge(['after', '--id', id]);
    new Notice('已归档；后台正在读这篇论文并更新专题体系'); this.refresh(); return file;
  }
  onunload() { this.controls.clear(); }
};
