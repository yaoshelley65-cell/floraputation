# Floraputation 品种索引库 (MVI) 维护指南

**版本: 2.0** | **最后更新: 2026-03-02**

---

## 1. 概述

**品种索引库 (Master Variety Index, MVI)** 是 Floraputation 平台的核心数据资产。它是一个存储在 `varieties.js` 文件中的 JavaScript 数组，名为 `MASTER_VARIETY_INDEX`。平台的所有搜索、过滤、图表生成和洞察分析功能均直接或间接地依赖于此数据。

本指南旨在为您提供清晰的说明，以便您能够独立地维护和扩展该索引库，确保平台数据的准确性和时效性。

## 2. 数据结构详解

索引库中的每一个对象都代表一个独立的植物品种，并包含以下字段。所有文本字段都应使用 **英文双引号 `""`** 包裹。

| 字段名 | 数据类型 | 是否必需 | 说明与示例 |
|---|---|---|---|
| `id` | Number | **是** | 唯一的整数标识符。新增品种时，请使用当前最大 ID + 1。 |
| `name` | String | **是** | **官方品种名称**，通常为“属名 + '品种名'”格式。这是主要的显示名称。<br>示例: `"Rosa 'Eden'"` |
| `aka` | String | 否 | **别名或商品名**。用于增强搜索匹配。<br>示例: `"Pierre de Ronsard"` |
| `zhName` | String | 否 | **中文通用名**。用于中文搜索和显示。<br>示例: `"伊甸玫瑰"` |
| `category` | String | **是** | **植物品类**。用于筛选和分类聚合。请保持品类名称的一致性。<br>示例: `"Rose"`, `"Hydrangea"` |
| `tags` | Array | 否 | **搜索标签数组**。包含描述品种特性的关键词，是模糊搜索和发现的关键。**强烈建议填写**。<br>示例: `["climbing", "fragrant", "award", "cut flower"]` |
| `score` | Number | **是** | **美誉度评分** (0-100)。核心指标。 |
| `trend` | String | **是** | **本月分数变化**。必须包含 `+` 或 `-` 符号。<br>示例: `"+4.2"`, `"-1.1"` |
| `trendDir` | String | **是** | **趋势方向**。可选值为 `"up"`, `"down"`, `"stable"`。 |
| `mentions` | Number | **是** | **过去12个月的总提及量**。整数。 |
| `pos` | Number | **是** | **正面情绪百分比** (0-100)。`pos`, `neu`, `neg` 三者之和应为 100。 |
| `neu` | Number | **是** | **中性情绪百分比** (0-100)。 |
| `neg` | Number | **是** | **负面情绪百分比** (0-100)。 |
| `region` | String | **是** | **主要市场区域**。用于地区筛选。<br>示例: `"Global"`, `"North America"`, `"Asia"` |
| `season` | String | 否 | **开花季节**。用于季节筛选。<br>示例: `"Spring/Summer"`, `"Autumn"` |
| `breeder` | String | 否 | **育种公司或个人**。用于搜索。<br>示例: `"David Austin"`, `"Meilland"` |
| `year` | Number | 否 | **引入年份** (近似值)。整数。 |
| `confidence` | String | 否 | **数据置信度**。可选值为 `"high"`, `"medium"`, `"low"`。低置信度品种会在卡片上显示警告。 |

## 3. 如何维护索引库

由于这是一个静态网站项目，所有数据维护都需要通过**直接编辑 `/floraputation/varieties.js` 文件**来完成。

### 3.1. 添加一个新品种

1.  **打开文件**: 在您的代码编辑器中打开 `/floraputation/varieties.js`。
2.  **定位末尾**: 滚动到 `MASTER_VARIETY_INDEX` 数组的末尾，在最后一个 `}` 和 `]` 之间。
3.  **添加逗号**: 在最后一个品种对象的 `}` 后面加上一个逗号 `,`。
4.  **粘贴新对象**: 在逗号后另起一行，粘贴一个新的、填写完整的品种对象（见下方示例）。
5.  **验证 ID**: 确保新品种的 `id` 是唯一的，并且比现有最大 ID 大 1。
6.  **保存文件**: 保存您的更改。

**示例：添加一个新的大丽花品种**

```javascript
// ... (前面的 120 个品种对象)
  {
    id: 120, 
    name: "Alstroemeria 'Inca Ice'", 
    // ... (id:120 的完整内容)
  },
  // 在这里添加新品种
  {
    id: 121, // 确保 ID 是唯一的，当前最大为 120，所以用 121
    name: "Dahlia 'Labyrinth'",
    aka: "Labyrinth Dahlia",
    zhName: "迷宫大丽花",
    category: "Dahlia",
    tags: ["bicolor", "pink orange", "dinner plate", "cut flower", "trending", "Instagram"],
    score: 89,
    trend: "+7.8",
    trendDir: "up",
    mentions: 15200,
    pos: 76,
    neu: 17,
    neg: 7,
    region: "Global",
    season: "Summer/Autumn",
    breeder: "Unknown",
    year: 2015,
    confidence: "medium"
  }
]; // 数组结束括号
```

### 3.2. 编辑一个现有品种

1.  **打开文件**: 打开 `/floraputation/varieties.js`。
2.  **搜索品种**: 使用编辑器的搜索功能 (Ctrl+F 或 Cmd+F) 查找您想编辑的品种名称，例如 `"Rosa 'Eden'"`。
3.  **修改字段**: 直接修改目标字段的值。例如，将 `score` 从 `87` 改为 `88`。
4.  **保存文件**: 保存您的更改。

### 3.3. 删除一个品种

1.  **打开文件**: 打开 `/floraputation/varieties.js`。
2.  **搜索品种**: 找到您想删除的品种对象。
3.  **删除对象**: 完整地选中从 `{` 到 `}` 的整个对象，包括它后面的逗号（如果它不是最后一个对象），然后删除。
4.  **保存文件**: 保存您的更改。

## 4. 搜索功能与标签策略

平台的搜索功能经过了优化，支持多字段、模糊匹配和拼写容错。为了让一个品种更容易被发现，**`tags` 字段至关重要**。

### 搜索匹配逻辑

搜索引擎会按以下优先级和字段进行匹配：

1.  **精确匹配**: `name`, `zhName`
2.  **前缀匹配**: `name`, `aka`, `zhName`
3.  **子串匹配**: `name`, `aka`, `zhName`, `category`, `breeder`
4.  **标签匹配**: `tags` 数组中的所有关键词
5.  **模糊匹配**: 对所有字段进行分词，允许 1-2 个字母的拼写错误 (Levenshtein 距离)

### 有效的标签策略

在 `tags` 数组中添加丰富的关键词可以极大地提升品种的可发现性。建议包含以下几类标签：

- **物理性状**: `climbing`, `dwarf`, `dark foliage`, `bicolor`, `ruffled`
- **颜色**: `soft pink`, `deep crimson`, `lime green`, `almost black`
- **气味**: `fragrant`, `rich scent`, `no scent`
- **用途**: `cut flower`, `dried`, `hedge`, `container`, `bedding`
- **荣誉/奖项**: `award`, `RHS`, `AARS`, `Perennial Plant of the Year`
- **流行趋势**: `trending`, `popular`, `Instagram`, `wedding`
- **文化/产地**: `Japanese`, `Chinese`, `heritage`, `classic`
- **维护/特性**: `disease resistant`, `heat tolerant`, `easy care`, `repeat bloom`

**一个好的标签示例：**

```javascript
  tags: ["english rose", "deep crimson", "fragrant", "David Austin", "rich scent", "award", "cut flower"]
```

---

完成任何修改后，只需刷新 Floraputation 网页即可看到更新。无需重启任何服务。
