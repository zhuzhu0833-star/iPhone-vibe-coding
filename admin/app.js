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

let catalog = { countries: [] };
let enabled = new Set();
let customSources = [];
let expanded = new Set();

const els = {
  countries: document.getElementById("countries"),
  stats: document.getElementById("stats"),
  search: document.getElementById("search"),
  status: document.getElementById("status"),
  customCountry: document.getElementById("custom-country"),
  customName: document.getElementById("custom-name"),
  customDomain: document.getElementById("custom-domain"),
  customList: document.getElementById("custom-list"),
  githubRepo: document.getElementById("github-repo"),
  githubToken: document.getElementById("github-token"),
};

function dataUrl(path) {
  return new URL(path, window.location.href).href;
}

async function loadData() {
  const [catalogRes, selectionsRes] = await Promise.all([
    fetch(dataUrl("data/catalog.json")),
    fetch(dataUrl("data/selections.json")),
  ]);
  if (!catalogRes.ok) throw new Error("无法加载 catalog.json");
  catalog = await catalogRes.json();

  const selections = selectionsRes.ok
    ? await selectionsRes.json()
    : { enabled_source_ids: [], custom_sources: [] };

  enabled = new Set(selections.enabled_source_ids || []);
  customSources = selections.custom_sources || [];

  if (enabled.size === 0) {
    for (const country of catalog.countries) {
      for (const source of country.sources) {
        enabled.add(source.id);
      }
    }
  }

  catalog.countries.forEach((c) => expanded.add(c.id));
  populateCustomCountrySelect();
  render();
}

function populateCustomCountrySelect() {
  els.customCountry.innerHTML = catalog.countries
    .map((c) => `<option value="${c.id}">${c.flag} ${c.name}</option>`)
    .join("");
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

function currentSelections() {
  return {
    enabled_source_ids: [...enabled].sort(),
    custom_sources: customSources,
  };
}

function updateStats() {
  const countryCount = catalog.countries.filter((country) =>
    country.sources.some((s) => enabled.has(s.id))
  ).length;
  const sourceCount = enabled.size + customSources.length;
  els.stats.textContent = `已启用 ${countryCount} 个国家 · ${sourceCount} 个来源`;
}

function setStatus(message, type = "") {
  els.status.textContent = message;
  els.status.className = `status ${type}`;
}

function matchesSearch(country, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  if (country.name.toLowerCase().includes(q)) return true;
  return country.sources.some((s) => s.name.toLowerCase().includes(q));
}

function countryEnabledCount(country) {
  return country.sources.filter((s) => enabled.has(s.id)).length;
}

function setCountrySources(countryId, checked) {
  const country = catalog.countries.find((c) => c.id === countryId);
  if (!country) return;
  for (const source of country.sources) {
    if (checked) enabled.add(source.id);
    else enabled.delete(source.id);
  }
  render();
}

function renderCustomList() {
  if (customSources.length === 0) {
    els.customList.innerHTML = "";
    return;
  }
  els.customList.innerHTML = customSources
    .map(
      (item, index) => `
      <li>
        <span>${item.name} <code>${item.domain || ""}</code></span>
        <button type="button" data-remove-custom="${index}">删除</button>
      </li>`
    )
    .join("");

  els.customList.querySelectorAll("[data-remove-custom]").forEach((btn) => {
    btn.addEventListener("click", () => {
      customSources.splice(Number(btn.dataset.removeCustom), 1);
      renderCustomList();
      updateStats();
    });
  });
}

function renderCountry(country) {
  const query = els.search.value.trim();
  if (!matchesSearch(country, query)) return "";

  const total = country.sources.length;
  const selected = countryEnabledCount(country);
  const isExpanded = expanded.has(country.id);
  const allChecked = selected === total && total > 0;
  const indeterminate = selected > 0 && selected < total;

  const groups = ["university", "education", "immigration"];
  const body = groups
    .map((type) => {
      const sources = country.sources.filter((s) => s.type === type);
      if (sources.length === 0) return "";
      const rows = sources
        .map(
          (source) => `
          <div class="source-row">
            <input
              type="checkbox"
              id="${source.id}"
              data-source-id="${source.id}"
              ${enabled.has(source.id) ? "checked" : ""}
            />
            <label for="${source.id}">
              <span class="source-name">${source.name}</span>
              <span class="source-type ${source.type}">${TYPE_LABELS[source.type]}</span>
            </label>
          </div>`
        )
        .join("");
      return `
        <div class="type-group">
          <div class="type-label">${TYPE_LABELS[type]}</div>
          ${rows}
        </div>`;
    })
    .join("");

  return `
    <section class="country-card" data-country-id="${country.id}">
      <div class="country-header" data-toggle-country="${country.id}">
        <input
          type="checkbox"
          data-country-checkbox="${country.id}"
          ${allChecked ? "checked" : ""}
          ${indeterminate ? 'data-indeterminate="true"' : ""}
        />
        <div class="country-title">${country.flag} ${country.name}</div>
        <div class="country-meta">${selected}/${total} · ${isExpanded ? "收起" : "展开"}</div>
      </div>
      <div class="country-body ${isExpanded ? "" : "hidden"}">${body}</div>
    </section>`;
}

function render() {
  els.countries.innerHTML = catalog.countries.map(renderCountry).join("");

  els.countries.querySelectorAll("[data-indeterminate='true']").forEach((box) => {
    box.indeterminate = true;
  });

  els.countries.querySelectorAll("[data-source-id]").forEach((box) => {
    box.addEventListener("change", () => {
      const id = box.dataset.sourceId;
      if (box.checked) enabled.add(id);
      else enabled.delete(id);
      render();
    });
  });

  els.countries.querySelectorAll("[data-country-checkbox]").forEach((box) => {
    box.addEventListener("click", (event) => event.stopPropagation());
    box.addEventListener("change", () => {
      setCountrySources(box.dataset.countryCheckbox, box.checked);
    });
  });

  els.countries.querySelectorAll("[data-toggle-country]").forEach((header) => {
    header.addEventListener("click", () => {
      const id = header.dataset.toggleCountry;
      if (expanded.has(id)) expanded.delete(id);
      else expanded.add(id);
      render();
    });
  });

  renderCustomList();
  updateStats();
}

function selectUniversitiesOnly() {
  enabled.clear();
  for (const country of catalog.countries) {
    for (const source of country.sources) {
      if (source.type === "university") enabled.add(source.id);
    }
  }
  render();
}

function selectAll() {
  enabled.clear();
  for (const country of catalog.countries) {
    for (const source of country.sources) {
      enabled.add(source.id);
    }
  }
  render();
}

function selectNone() {
  enabled.clear();
  render();
}

function addCustomSource() {
  const countryId = els.customCountry.value;
  const name = els.customName.value.trim();
  const domain = els.customDomain.value.trim().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
  if (!name || !domain) {
    setStatus("请填写院校名称和官网域名", "err");
    return;
  }

  const id = `custom-${countryId}-${slugify(name)}`;
  customSources.push({
    id,
    country_id: countryId,
    name,
    domain,
    type: "university",
    url: buildGoogleNewsUrl(domain, countryId),
  });

  els.customName.value = "";
  els.customDomain.value = "";
  setStatus(`已添加 ${name}，记得保存配置`, "ok");
  render();
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
  setStatus("已下载 selections.json，请上传到仓库 data/ 目录", "ok");
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
    if (getRes.ok) {
      const existing = await getRes.json();
      sha = existing.sha;
    }

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
    setStatus("已保存！下次 Actions 运行将使用新来源。", "ok");
  } catch (error) {
    setStatus(`保存失败：${error.message}`, "err");
  }
}

document.getElementById("btn-universities").addEventListener("click", selectUniversitiesOnly);
document.getElementById("btn-all").addEventListener("click", selectAll);
document.getElementById("btn-none").addEventListener("click", selectNone);
document.getElementById("btn-add-custom").addEventListener("click", addCustomSource);
document.getElementById("btn-download").addEventListener("click", downloadSelections);
document.getElementById("btn-save-github").addEventListener("click", saveToGitHub);
els.search.addEventListener("input", render);

const savedRepo = localStorage.getItem("digest-admin-repo");
if (savedRepo) els.githubRepo.value = savedRepo;

loadData().catch((error) => {
  setStatus(`加载失败：${error.message}`, "err");
});
