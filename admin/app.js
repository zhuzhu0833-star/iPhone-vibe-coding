const TYPE_LABELS = {
  university: "高校",
  education: "教育部门",
  immigration: "移民机构",
};

const GOOGLE_NEWS_LOCALE = {
  us: { hl: "en-US", gl: "US", ceid: "US:en" },
  uk: { hl: "en-GB", gl: "GB", ceid: "GB:en" },
  au: { hl: "en-AU", gl: "AU", ceid: "AU:en" },
  ca: { hl: "en-CA", gl: "CA", ceid: "CA:en" },
  nz: { hl: "en-NZ", gl: "NZ", ceid: "NZ:en" },
  ie: { hl: "en-IE", gl: "IE", ceid: "IE:en" },
  hk: { hl: "en", gl: "HK", ceid: "HK:en" },
  sg: { hl: "en", gl: "SG", ceid: "SG:en" },
  my: { hl: "en", gl: "MY", ceid: "MY:en" },
  nl: { hl: "en", gl: "NL", ceid: "NL:en" },
  no: { hl: "en", gl: "NO", ceid: "NO:en" },
  se: { hl: "en", gl: "SE", ceid: "SE:en" },
  dk: { hl: "en", gl: "DK", ceid: "DK:en" },
  fi: { hl: "en", gl: "FI", ceid: "FI:en" },
};

const state = {
  catalog: { countries: [] },
  enabled: new Set(),
  customSources: [],
  expanded: new Set(),
  savedSnapshot: "",
  typeFilter: "all",
  activeCountry: null,
  highlightSourceId: null,
};

const els = {
  countries: document.getElementById("countries"),
  countryNav: document.getElementById("country-nav"),
  search: document.getElementById("search"),
  emptyState: document.getElementById("empty-state"),
  statCountries: document.getElementById("stat-countries"),
  statSources: document.getElementById("stat-sources"),
  statUniversities: document.getElementById("stat-universities"),
  progressText: document.getElementById("progress-text"),
  progressFill: document.getElementById("progress-fill"),
  dirtyBadge: document.getElementById("dirty-badge"),
  dockSummary: document.getElementById("dock-summary"),
  customCountry: document.getElementById("custom-country"),
  customName: document.getElementById("custom-name"),
  customDomain: document.getElementById("custom-domain"),
  customList: document.getElementById("custom-list"),
  githubRepo: document.getElementById("github-repo"),
  githubToken: document.getElementById("github-token"),
  status: document.getElementById("status"),
  saveDialog: document.getElementById("save-dialog"),
  toast: document.getElementById("toast"),
};

function dataUrl(path) {
  return new URL(path, window.location.href).href;
}

function snapshotSelections() {
  return JSON.stringify(currentSelections());
}

function markSaved() {
  state.savedSnapshot = snapshotSelections();
  updateDock();
}

function isDirty() {
  return snapshotSelections() !== state.savedSnapshot;
}

function currentSelections() {
  return {
    enabled_source_ids: [...state.enabled].sort(),
    custom_sources: state.customSources,
  };
}

function showToast(message, type = "") {
  els.toast.textContent = message;
  els.toast.className = `toast ${type}`.trim();
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => {
    els.toast.className = "toast hidden";
  }, 2800);
}

function setStatus(message, type = "") {
  els.status.textContent = message;
  els.status.className = `status ${type}`;
}

function sourcesForCountry(country) {
  const catalogSources = country.sources.map((source) => ({
    ...source,
    isCustom: false,
  }));
  const custom = state.customSources
    .filter((item) => item.country_id === country.id)
    .map((item) => ({
      id: item.id,
      name: item.name,
      type: item.type || "university",
      url: item.url,
      domain: item.domain,
      isCustom: true,
    }));
  return [...catalogSources, ...custom];
}

function countryById(id) {
  return state.catalog.countries.find((c) => c.id === id);
}

function isSourceEnabled(source) {
  return source.isCustom || state.enabled.has(source.id);
}

function countryEnabledCount(country) {
  return sourcesForCountry(country).filter(isSourceEnabled).length;
}

function matchesSearch(country, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  if (country.name.toLowerCase().includes(q)) return true;
  return sourcesForCountry(country).some((s) => s.name.toLowerCase().includes(q));
}

function sourceVisible(source) {
  return state.typeFilter === "all" || source.type === state.typeFilter;
}

function visibleSources(country) {
  return sourcesForCountry(country).filter(sourceVisible);
}

function buildGoogleNewsUrl(domain, countryId) {
  const locale = GOOGLE_NEWS_LOCALE[countryId] || GOOGLE_NEWS_LOCALE.us;
  const query = encodeURIComponent(
    `site:${domain} international student OR admission OR tuition`
  );
  return `https://news.google.com/rss/search?q=${query}&hl=${locale.hl}&gl=${locale.gl}&ceid=${locale.ceid}`;
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);
}

async function loadData() {
  const [catalogRes, selectionsRes] = await Promise.all([
    fetch(dataUrl("data/catalog.json")),
    fetch(dataUrl("data/selections.json")),
  ]);
  if (!catalogRes.ok) throw new Error("无法加载 catalog.json");

  state.catalog = await catalogRes.json();
  const selections = selectionsRes.ok
    ? await selectionsRes.json()
    : { enabled_source_ids: [], custom_sources: [] };

  state.enabled = new Set(selections.enabled_source_ids || []);
  state.customSources = selections.custom_sources || [];

  if (state.enabled.size === 0) {
    for (const country of state.catalog.countries) {
      for (const source of country.sources) state.enabled.add(source.id);
    }
  }

  state.catalog.countries.forEach((c) => state.expanded.add(c.id));
  state.activeCountry = state.catalog.countries[0]?.id || null;
  populateCustomCountrySelect();
  markSaved();

  const savedRepo = localStorage.getItem("digest-admin-repo");
  if (savedRepo) els.githubRepo.value = savedRepo;

  renderAll();
}

function populateCustomCountrySelect() {
  els.customCountry.innerHTML = state.catalog.countries
    .map((c) => `<option value="${c.id}">${c.flag} ${c.name}</option>`)
    .join("");
}

function setCountrySources(countryId, checked, type = null) {
  const country = countryById(countryId);
  if (!country) return;
  for (const source of sourcesForCountry(country)) {
    if (source.isCustom) continue;
    if (type && source.type !== type) continue;
    if (checked) state.enabled.add(source.id);
    else state.enabled.delete(source.id);
  }
  renderAll();
}

function updateStats() {
  const countries = state.catalog.countries;
  const countryCount = countries.filter((c) =>
    sourcesForCountry(c).some(isSourceEnabled)
  ).length;

  const universityCount = countries.reduce((sum, country) => {
    return (
      sum +
      sourcesForCountry(country).filter(
        (s) => s.type === "university" && isSourceEnabled(s)
      ).length
    );
  }, 0);

  const totalCatalog = countries.reduce(
    (sum, c) => sum + sourcesForCountry(c).length,
    0
  );
  const selected = countries.reduce(
    (sum, c) => sum + sourcesForCountry(c).filter(isSourceEnabled).length,
    0
  );
  const total = totalCatalog;
  const pct = total ? Math.round((selected / total) * 100) : 0;

  els.statCountries.textContent = String(countryCount);
  els.statSources.textContent = String(selected);
  els.statUniversities.textContent = String(universityCount);
  els.progressText.textContent = `${selected} / ${total}`;
  els.progressFill.style.width = `${pct}%`;
}

function updateDock() {
  const dirty = isDirty();
  els.dirtyBadge.classList.toggle("hidden", !dirty);
  els.dockSummary.textContent = dirty
    ? "更改尚未保存，请保存到 GitHub 或下载 JSON"
    : "所有更改已同步，可直接关闭页面";
}

function renderNav() {
  const query = els.search.value.trim();
  els.countryNav.innerHTML = state.catalog.countries
    .filter((country) => matchesSearch(country, query))
    .map((country) => {
      const sources = sourcesForCountry(country);
      const selected = countryEnabledCount(country);
      const total = sources.length;
      const customCount = sources.filter((s) => s.isCustom).length;
      const customBadge =
        customCount > 0 ? ` · +${customCount}自定义` : "";
      return `
        <button
          type="button"
          class="nav-item ${state.activeCountry === country.id ? "active" : ""}"
          data-nav-country="${country.id}"
        >
          <span>${country.flag} ${country.name}</span>
          <span class="nav-count">${selected}/${total}${customBadge}</span>
        </button>`;
    })
    .join("");
}

function renderCountryCard(country) {
  const query = els.search.value.trim();
  if (!matchesSearch(country, query)) return "";

  const sources = sourcesForCountry(country);
  const visible = visibleSources(country);
  if (visible.length === 0) return "";

  const total = sources.length;
  const selected = countryEnabledCount(country);
  const isExpanded = state.expanded.has(country.id);
  const catalogSources = sources.filter((s) => !s.isCustom);
  const allCatalogChecked =
    catalogSources.length > 0 &&
    catalogSources.every((s) => state.enabled.has(s.id));
  const indeterminate = selected > 0 && !allCatalogChecked;
  const dimmed = state.activeCountry && state.activeCountry !== country.id;

  const groups = ["university", "education", "immigration"]
    .map((type) => {
      const groupSources = sources.filter((s) => s.type === type && sourceVisible(s));
      if (groupSources.length === 0) return "";

      const rows = groupSources
        .map((source) => {
          const checked = isSourceEnabled(source);
          const highlight = source.id === state.highlightSourceId ? " source-new" : "";
          const customBadge = source.isCustom
            ? '<span class="source-type custom">自定义</span>'
            : `<span class="source-type ${source.type}">${TYPE_LABELS[type]}</span>`;
          const customActions = source.isCustom
            ? `<button type="button" class="btn ghost sm source-remove" data-remove-source="${source.id}">删除</button>`
            : "";

          return `
            <div class="source-card ${checked ? "checked" : ""}${highlight}" data-source-card="${source.id}">
              <label class="source-card-main">
                <input
                  type="checkbox"
                  data-source-id="${source.id}"
                  data-is-custom="${source.isCustom ? "1" : "0"}"
                  ${checked ? "checked" : ""}
                  ${source.isCustom ? "disabled" : ""}
                />
                <span>
                  <span class="source-name">${source.name}</span>
                  ${customBadge}
                  ${source.isCustom && source.domain ? `<span class="source-domain">${source.domain}</span>` : ""}
                </span>
              </label>
              ${customActions}
            </div>`;
        })
        .join("");

      return `
        <section class="type-group" data-type-group="${type}">
          <div class="type-header">
            <span class="type-label">${TYPE_LABELS[type]}</span>
            <button type="button" class="type-select" data-type-toggle="${country.id}:${type}">
              全选此类
            </button>
          </div>
          <div class="source-grid">${rows}</div>
        </section>`;
    })
    .join("");

  return `
    <section class="country-card ${dimmed ? "dimmed" : ""}" id="country-${country.id}" data-country-id="${country.id}">
      <div class="country-header">
        <input
          type="checkbox"
          data-country-checkbox="${country.id}"
          ${allCatalogChecked && selected === total ? "checked" : ""}
          ${indeterminate ? 'data-indeterminate="true"' : ""}
          aria-label="选择 ${country.name} 全部来源"
        />
        <div class="country-title">${country.flag} ${country.name}</div>
        <div class="country-meta">已选 ${selected} / ${total}</div>
        <button
          type="button"
          class="chevron-btn"
          data-toggle-country="${country.id}"
          aria-expanded="${isExpanded}"
          aria-label="${isExpanded ? "收起" : "展开"} ${country.name}"
        >${isExpanded ? "▾" : "▸"}</button>
      </div>
      <div class="country-body ${isExpanded ? "" : "hidden"}">${groups}</div>
    </section>`;
}

function renderCountries() {
  const html = state.catalog.countries.map(renderCountryCard).filter(Boolean).join("");
  els.countries.innerHTML = html;
  els.emptyState.classList.toggle("hidden", Boolean(html));

  els.countries.querySelectorAll("[data-indeterminate='true']").forEach((box) => {
    box.indeterminate = true;
  });
}

function renderCustomList() {
  if (state.customSources.length === 0) {
    els.customList.innerHTML = `<li class="hint">暂无自定义院校，添加后会显示在对应国家的高校列表中</li>`;
    return;
  }

  els.customList.innerHTML = state.customSources
    .map((item) => {
      const country = countryById(item.country_id);
      return `
      <li>
        <span>
          ${country ? `${country.flag} ` : ""}${item.name}
          <code>${item.domain || ""}</code>
        </span>
        <span class="custom-list-actions">
          <button type="button" class="btn ghost sm" data-jump-source="${item.id}">查看</button>
          <button type="button" class="btn ghost sm" data-remove-custom-id="${item.id}">删除</button>
        </span>
      </li>`;
    })
    .join("");
}

function renderAll() {
  renderNav();
  renderCountries();
  renderCustomList();
  updateStats();
  updateDock();
}

function scrollToCountry(countryId, sourceId = null) {
  state.activeCountry = countryId;
  state.expanded.add(countryId);
  if (sourceId) state.highlightSourceId = sourceId;
  renderAll();
  const node = document.getElementById(`country-${countryId}`);
  if (node) node.scrollIntoView({ behavior: "smooth", block: "start" });
  if (sourceId) {
    setTimeout(() => {
      const sourceNode = document.querySelector(`[data-source-card="${sourceId}"]`);
      if (sourceNode) sourceNode.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 120);
    setTimeout(() => {
      state.highlightSourceId = null;
      renderCountries();
    }, 2400);
  }
}

function selectUniversitiesOnly() {
  state.enabled.clear();
  for (const country of state.catalog.countries) {
    for (const source of country.sources) {
      if (source.type === "university") state.enabled.add(source.id);
    }
  }
  showToast("已仅选择高校来源");
  renderAll();
}

function selectUniversitiesAndEducation() {
  state.enabled.clear();
  for (const country of state.catalog.countries) {
    for (const source of country.sources) {
      if (source.type === "university" || source.type === "education") {
        state.enabled.add(source.id);
      }
    }
  }
  showToast("已选择高校 + 教育部门");
  renderAll();
}

function selectAll() {
  state.enabled.clear();
  for (const country of state.catalog.countries) {
    for (const source of country.sources) state.enabled.add(source.id);
  }
  showToast("已全选所有来源");
  renderAll();
}

function selectNone() {
  state.enabled.clear();
  showToast("已清空所有选择");
  renderAll();
}

function addCustomSource() {
  const countryId = els.customCountry.value;
  const name = els.customName.value.trim();
  const domain = els.customDomain.value
    .trim()
    .replace(/^https?:\/\//, "")
    .replace(/\/.*$/, "");

  if (!name || !domain) {
    showToast("请填写院校名称和官网域名", "err");
    return;
  }

  const id = `custom-${countryId}-${slugify(name)}`;
  if (
    state.customSources.some((item) => item.id === id) ||
    state.catalog.countries.some((country) =>
      country.sources.some((source) => source.id === id)
    )
  ) {
    showToast("该院校来源已存在", "err");
    return;
  }

  state.customSources.push({
    id,
    country_id: countryId,
    name,
    domain,
    type: "university",
    url: buildGoogleNewsUrl(domain, countryId),
  });

  els.customName.value = "";
  els.customDomain.value = "";
  state.highlightSourceId = id;
  state.activeCountry = countryId;
  state.expanded.add(countryId);
  state.typeFilter = "all";
  document.querySelectorAll(".filter-chips .chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.filter === "all");
  });

  showToast(`已添加 ${name}，已显示在 ${countryById(countryId)?.name || "对应国家"}`, "ok");
  renderAll();

  setTimeout(() => {
    const node = document.querySelector(`[data-source-card="${id}"]`);
    if (node) node.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 50);

  setTimeout(() => {
    state.highlightSourceId = null;
    renderCountries();
  }, 2400);
}

function removeCustomSource(sourceId) {
  const index = state.customSources.findIndex((item) => item.id === sourceId);
  if (index === -1) return;
  const name = state.customSources[index].name;
  state.customSources.splice(index, 1);
  showToast(`已删除 ${name}`);
  renderAll();
}

function downloadSelections() {
  const blob = new Blob([JSON.stringify(currentSelections(), null, 2) + "\n"], {
    type: "application/json",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "selections.json";
  link.click();
  URL.revokeObjectURL(link.href);
  showToast("已下载 selections.json", "ok");
}

function toBase64Utf8(text) {
  return btoa(String.fromCharCode(...new TextEncoder().encode(text)));
}

async function saveToGitHub() {
  const token = els.githubToken.value.trim();
  const repo = els.githubRepo.value.trim();

  if (!token) {
    setStatus("请填写 GitHub Personal Access Token", "err");
    return;
  }
  if (!repo.includes("/")) {
    setStatus("仓库格式应为 owner/repo", "err");
    return;
  }

  const [owner, repoName] = repo.split("/");
  const path = "data/selections.json";
  const content = JSON.stringify(currentSelections(), null, 2) + "\n";
  setStatus("正在保存到 GitHub…", "");

  try {
    const headers = {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    };

    let sha;
    const getRes = await fetch(
      `https://api.github.com/repos/${owner}/${repoName}/contents/${path}`,
      { headers }
    );
    if (getRes.ok) sha = (await getRes.json()).sha;

    const putRes = await fetch(
      `https://api.github.com/repos/${owner}/${repoName}/contents/${path}`,
      {
        method: "PUT",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "chore: update news source selections from admin panel",
          content: toBase64Utf8(content),
          sha,
        }),
      }
    );

    if (!putRes.ok) {
      const err = await putRes.json();
      throw new Error(err.message || "GitHub API 保存失败");
    }

    localStorage.setItem("digest-admin-repo", repo);
    sessionStorage.setItem("digest-admin-token", token);
    markSaved();
    setStatus("保存成功！下次日报将使用新来源。", "ok");
    showToast("已保存到 GitHub", "ok");
    els.saveDialog.close();
  } catch (error) {
    setStatus(`保存失败：${error.message}`, "err");
    showToast(`保存失败：${error.message}`, "err");
  }
}

function openSaveDialog() {
  const savedToken = sessionStorage.getItem("digest-admin-token");
  if (savedToken && !els.githubToken.value) els.githubToken.value = savedToken;
  els.saveDialog.showModal();
}

els.countries.addEventListener("change", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) return;

  if (target.dataset.sourceId && target.dataset.isCustom !== "1") {
    if (target.checked) state.enabled.add(target.dataset.sourceId);
    else state.enabled.delete(target.dataset.sourceId);
    target.closest(".source-card")?.classList.toggle("checked", target.checked);
    updateStats();
    updateDock();
    renderNav();
    return;
  }

  if (target.dataset.countryCheckbox) {
    setCountrySources(target.dataset.countryCheckbox, target.checked);
  }
});

els.countries.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const toggle = target.closest("[data-toggle-country]");
  if (toggle) {
    const id = toggle.getAttribute("data-toggle-country");
    if (state.expanded.has(id)) state.expanded.delete(id);
    else state.expanded.add(id);
    renderCountries();
    return;
  }

  const typeToggle = target.closest("[data-type-toggle]");
  if (typeToggle) {
    const [countryId, type] = typeToggle.getAttribute("data-type-toggle").split(":");
    const country = countryById(countryId);
    const sources = sourcesForCountry(country).filter(
      (s) => s.type === type && !s.isCustom
    );
    const allOn = sources.every((s) => state.enabled.has(s.id));
    setCountrySources(countryId, !allOn, type);
    return;
  }

  const removeBtn = target.closest("[data-remove-source]");
  if (removeBtn) {
    removeCustomSource(removeBtn.getAttribute("data-remove-source"));
  }
});

els.countryNav.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-nav-country]");
  if (!btn) return;
  scrollToCountry(btn.getAttribute("data-nav-country"));
});

document.querySelectorAll(".filter-chips .chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".filter-chips .chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    state.typeFilter = chip.dataset.filter;
    renderAll();
  });
});

document.getElementById("btn-universities").addEventListener("click", selectUniversitiesOnly);
document.getElementById("btn-uni-edu").addEventListener("click", selectUniversitiesAndEducation);
document.getElementById("btn-all").addEventListener("click", selectAll);
document.getElementById("btn-none").addEventListener("click", selectNone);
document.getElementById("btn-expand-all").addEventListener("click", () => {
  state.catalog.countries.forEach((c) => state.expanded.add(c.id));
  renderCountries();
});
document.getElementById("btn-collapse-all").addEventListener("click", () => {
  state.expanded.clear();
  renderCountries();
});
document.getElementById("btn-add-custom").addEventListener("click", addCustomSource);
document.getElementById("btn-download").addEventListener("click", downloadSelections);
document.getElementById("btn-save-github").addEventListener("click", openSaveDialog);
document.getElementById("btn-open-save").addEventListener("click", openSaveDialog);
document.getElementById("btn-save-dialog").addEventListener("click", saveToGitHub);
document.getElementById("btn-close-dialog").addEventListener("click", () => els.saveDialog.close());
document.getElementById("btn-close-dialog-2").addEventListener("click", () => els.saveDialog.close());
document.getElementById("btn-toggle-token").addEventListener("click", () => {
  const input = els.githubToken;
  input.type = input.type === "password" ? "text" : "password";
});

els.customList.addEventListener("click", (event) => {
  const jumpBtn = event.target.closest("[data-jump-source]");
  if (jumpBtn) {
    const item = state.customSources.find((s) => s.id === jumpBtn.dataset.jumpSource);
    if (item) scrollToCountry(item.country_id);
    return;
  }

  const removeBtn = event.target.closest("[data-remove-custom-id]");
  if (removeBtn) removeCustomSource(removeBtn.dataset.removeCustomId);
});

els.search.addEventListener("input", renderAll);

els.customName.addEventListener("keydown", (event) => {
  if (event.key === "Enter") addCustomSource();
});
els.customDomain.addEventListener("keydown", (event) => {
  if (event.key === "Enter") addCustomSource();
});

window.addEventListener("beforeunload", (event) => {
  if (isDirty()) {
    event.preventDefault();
    event.returnValue = "";
  }
});

loadData().catch((error) => {
  showToast(`加载失败：${error.message}`, "err");
});
