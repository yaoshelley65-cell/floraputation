/* ============================================================
   Floraputation — Master Variety Index (MVI)
   Version: 2.0 | Last Updated: 2026-03
   Total Varieties: 120+
   
   FIELD REFERENCE:
   id        — Unique integer identifier
   name      — Official cultivar name (Latin + cultivar epithet)
   aka       — Common name / trade name / breeder name
   zhName    — Chinese common name (中文名)
   category  — Plant genus / common category
   tags      — Searchable keyword tags (traits, use cases, awards)
   score     — Reputation Index (0–100)
   trend     — Score change this month (e.g. "+3.2" or "-1.1")
   trendDir  — "up" | "down" | "stable"
   mentions  — Total mentions in last 12 months
   pos       — % Positive sentiment
   neu       — % Neutral sentiment
   neg       — % Negative sentiment
   region    — Primary market region
   season    — Bloom season
   breeder   — Breeding company / originator
   year      — Year of introduction (approx.)
   confidence— Data confidence level: "high" | "medium" | "low"
   ============================================================ */

const MASTER_VARIETY_INDEX = [

  // ============================================================
  // ROSE — 玫瑰 / 月季
  // ============================================================
  { id: 1,   name: "Rosa 'Eden'",               aka: "Pierre de Ronsard",        zhName: "伊甸玫瑰",   category: "Rose",          tags: ["climbing","fragrant","award","romantic","cut flower","repeat bloom"],    score: 87, trend: "+4.2", trendDir: "up",     mentions: 48320, pos: 72, neu: 19, neg: 9,  region: "Global",        season: "Spring/Summer", breeder: "Meilland",   year: 1985, confidence: "high" },
  { id: 2,   name: "Rosa 'Queen Elizabeth'",     aka: "The Queen Elizabeth Rose", zhName: "伊丽莎白女王", category: "Rose",          tags: ["grandiflora","pink","disease resistant","classic","cut flower"],         score: 81, trend: "-1.1", trendDir: "down",   mentions: 31450, pos: 65, neu: 21, neg: 14, region: "North America", season: "Summer",        breeder: "Lammerts",   year: 1954, confidence: "high" },
  { id: 3,   name: "Rosa 'Black Baccara'",       aka: "Black Baccara",            zhName: "黑巴卡拉",    category: "Rose",          tags: ["dark red","velvet","cut flower","florist","dramatic","hybrid tea"],       score: 78, trend: "+0.7", trendDir: "up",     mentions: 18900, pos: 62, neu: 25, neg: 13, region: "Europe",        season: "Summer",        breeder: "Meilland",   year: 2000, confidence: "high" },
  { id: 4,   name: "Rosa 'Olivia'",              aka: "Olivia Rose Austin",       zhName: "奥利维亚",    category: "Rose",          tags: ["english rose","soft pink","fragrant","repeat bloom","David Austin"],      score: 85, trend: "+9.8", trendDir: "up",     mentions: 6100,  pos: 74, neu: 18, neg: 8,  region: "Global",        season: "Spring/Summer", breeder: "David Austin", year: 2014, confidence: "medium" },
  { id: 5,   name: "Rosa 'Double Delight'",      aka: "Double Delight",           zhName: "双重喜悦",    category: "Rose",          tags: ["bicolor","fragrant","award","hybrid tea","red white"],                    score: 71, trend: "-3.9", trendDir: "down",   mentions: 18100, pos: 58, neu: 24, neg: 18, region: "North America", season: "Summer",        breeder: "Swim & Ellis", year: 1977, confidence: "high" },
  { id: 6,   name: "Rosa 'Falstaff'",            aka: "Falstaff",                 zhName: "福斯塔夫",    category: "Rose",          tags: ["english rose","deep crimson","fragrant","shrub","David Austin"],          score: 82, trend: "+1.8", trendDir: "up",     mentions: 12400, pos: 68, neu: 22, neg: 10, region: "Europe",        season: "Spring/Summer", breeder: "David Austin", year: 1999, confidence: "medium" },
  { id: 7,   name: "Rosa 'Graham Thomas'",       aka: "Graham Thomas",            zhName: "格雷厄姆·托马斯", category: "Rose",       tags: ["english rose","yellow","fragrant","shrub","David Austin","award"],       score: 86, trend: "+2.3", trendDir: "up",     mentions: 21300, pos: 71, neu: 20, neg: 9,  region: "Global",        season: "Spring/Summer", breeder: "David Austin", year: 1983, confidence: "high" },
  { id: 8,   name: "Rosa 'Iceberg'",             aka: "Schneewittchen",           zhName: "冰山玫瑰",    category: "Rose",          tags: ["floribunda","white","disease resistant","prolific","classic"],             score: 84, trend: "+1.5", trendDir: "up",     mentions: 26700, pos: 70, neu: 21, neg: 9,  region: "Global",        season: "Summer/Autumn", breeder: "Kordes",     year: 1958, confidence: "high" },
  { id: 9,   name: "Rosa 'Juliet'",              aka: "Juliet Rose",              zhName: "朱丽叶玫瑰",  category: "Rose",          tags: ["english rose","peach apricot","fragrant","David Austin","wedding"],        score: 89, trend: "+5.1", trendDir: "up",     mentions: 35600, pos: 77, neu: 16, neg: 7,  region: "Global",        season: "Spring/Summer", breeder: "David Austin", year: 2006, confidence: "high" },
  { id: 10,  name: "Rosa 'Knock Out'",           aka: "Knock Out Rose",           zhName: "淘汰赛玫瑰",  category: "Rose",          tags: ["shrub","disease resistant","low maintenance","red","repeat bloom"],        score: 83, trend: "+2.0", trendDir: "up",     mentions: 29800, pos: 69, neu: 22, neg: 9,  region: "North America", season: "Spring/Autumn", breeder: "Radler",     year: 2000, confidence: "high" },
  { id: 11,  name: "Rosa 'Lady of Shalott'",     aka: "Lady of Shalott",          zhName: "夏洛特小姐",  category: "Rose",          tags: ["english rose","salmon orange","fragrant","David Austin","repeat bloom"],   score: 87, trend: "+3.4", trendDir: "up",     mentions: 18900, pos: 73, neu: 19, neg: 8,  region: "Global",        season: "Spring/Summer", breeder: "David Austin", year: 2009, confidence: "medium" },
  { id: 12,  name: "Rosa 'Mr. Lincoln'",         aka: "Mister Lincoln",           zhName: "林肯先生",    category: "Rose",          tags: ["hybrid tea","dark red","fragrant","classic","award","cut flower"],         score: 79, trend: "-0.5", trendDir: "down",   mentions: 14200, pos: 64, neu: 25, neg: 11, region: "North America", season: "Summer",        breeder: "Swim & Weeks", year: 1964, confidence: "medium" },
  { id: 13,  name: "Rosa 'Munstead Wood'",       aka: "Munstead Wood",            zhName: "芒斯特德伍德", category: "Rose",         tags: ["english rose","deep crimson","fragrant","David Austin","rich scent"],       score: 88, trend: "+4.0", trendDir: "up",     mentions: 16700, pos: 75, neu: 17, neg: 8,  region: "Europe",        season: "Spring/Summer", breeder: "David Austin", year: 2007, confidence: "medium" },
  { id: 14,  name: "Rosa 'Peace'",               aka: "Gloria Dei",               zhName: "和平玫瑰",    category: "Rose",          tags: ["hybrid tea","yellow pink","classic","award","historic"],                   score: 80, trend: "-0.3", trendDir: "stable",  mentions: 22100, pos: 66, neu: 24, neg: 10, region: "Global",        season: "Summer",        breeder: "Meilland",   year: 1945, confidence: "high" },
  { id: 15,  name: "Rosa 'Rhapsody in Blue'",    aka: "Rhapsody in Blue",         zhName: "蓝色狂想曲",  category: "Rose",          tags: ["purple blue","fragrant","shrub","unique color","unusual"],                 score: 76, trend: "+1.2", trendDir: "up",     mentions: 9800,  pos: 61, neu: 27, neg: 12, region: "Europe",        season: "Summer",        breeder: "Cowlishaw",  year: 2002, confidence: "medium" },
  { id: 16,  name: "Rosa 'Yves Piaget'",         aka: "Yves Piaget",              zhName: "伊芙伯爵",    category: "Rose",          tags: ["hybrid tea","deep pink","fragrant","award","peony-like","cut flower"],     score: 91, trend: "+5.8", trendDir: "up",     mentions: 41200, pos: 80, neu: 14, neg: 6,  region: "Asia",          season: "Spring/Summer", breeder: "Meilland",   year: 1984, confidence: "high" },
  { id: 17,  name: "Rosa 'Blue Moon'",           aka: "Mainzer Fastnacht",        zhName: "蓝月亮",      category: "Rose",          tags: ["hybrid tea","lilac","fragrant","award","cut flower","unique"],              score: 77, trend: "+0.9", trendDir: "up",     mentions: 11300, pos: 62, neu: 26, neg: 12, region: "Europe",        season: "Summer",        breeder: "Tantau",     year: 1964, confidence: "medium" },
  { id: 18,  name: "Rosa 'Constance Spry'",      aka: "Constance Spry",           zhName: "康斯坦斯·斯普里", category: "Rose",      tags: ["english rose","pink","fragrant","once blooming","David Austin","historic"], score: 78, trend: "+0.4", trendDir: "up",    mentions: 8900,  pos: 63, neu: 27, neg: 10, region: "Europe",        season: "Spring",        breeder: "David Austin", year: 1961, confidence: "medium" },
  { id: 19,  name: "Rosa 'Darcey Bussell'",      aka: "Darcey Bussell",           zhName: "达西·布塞尔", category: "Rose",          tags: ["english rose","crimson","fragrant","David Austin","compact"],              score: 84, trend: "+2.6", trendDir: "up",     mentions: 13400, pos: 70, neu: 21, neg: 9,  region: "Europe",        season: "Spring/Summer", breeder: "David Austin", year: 2006, confidence: "medium" },
  { id: 20,  name: "Rosa 'The Generous Gardener'", aka: "The Generous Gardener", zhName: "慷慨的园丁",  category: "Rose",          tags: ["english rose","pale pink","fragrant","climbing","David Austin"],           score: 85, trend: "+3.1", trendDir: "up",     mentions: 14800, pos: 72, neu: 20, neg: 8,  region: "Europe",        season: "Spring/Summer", breeder: "David Austin", year: 2002, confidence: "medium" },

  // ============================================================
  // CHRYSANTHEMUM — 菊花
  // ============================================================
  { id: 21,  name: "Chrysanthemum 'Zembla'",     aka: "Zembla Chrysanthemum",     zhName: "赞布拉菊",    category: "Chrysanthemum", tags: ["cut flower","white","large bloom","florist","long vase life"],            score: 84, trend: "+2.8", trendDir: "up",     mentions: 27600, pos: 70, neu: 20, neg: 10, region: "Europe",        season: "Autumn",        breeder: "Fides",      year: 1990, confidence: "high" },
  { id: 22,  name: "Chrysanthemum 'Anastasia'",  aka: "Anastasia",                zhName: "阿纳斯塔西娅菊", category: "Chrysanthemum", tags: ["spider","mauve","unique form","cut flower","florist"],                score: 80, trend: "+2.1", trendDir: "up",     mentions: 24500, pos: 66, neu: 22, neg: 12, region: "Global",        season: "Autumn",        breeder: "Unknown",    year: 1995, confidence: "high" },
  { id: 23,  name: "Chrysanthemum 'Fuji'",       aka: "Fuji Mum",                 zhName: "富士菊",      category: "Chrysanthemum", tags: ["spider","white","Japanese","show","exhibition"],                           score: 68, trend: "-3.1", trendDir: "down",   mentions: 12400, pos: 55, neu: 30, neg: 15, region: "Asia",          season: "Autumn",        breeder: "Japan",      year: 1970, confidence: "medium" },
  { id: 24,  name: "Chrysanthemum 'Shamrock'",   aka: "Shamrock",                 zhName: "三叶草菊",    category: "Chrysanthemum", tags: ["button","green","unique","florist","novelty"],                             score: 79, trend: "+1.4", trendDir: "up",     mentions: 16800, pos: 64, neu: 25, neg: 11, region: "Global",        season: "Autumn",        breeder: "Fides",      year: 2000, confidence: "medium" },
  { id: 25,  name: "Chrysanthemum 'Kermit'",     aka: "Kermit Mum",               zhName: "科米特菊",    category: "Chrysanthemum", tags: ["button","green","popular","florist","long lasting"],                       score: 82, trend: "+2.4", trendDir: "up",     mentions: 21300, pos: 68, neu: 23, neg: 9,  region: "Global",        season: "Autumn",        breeder: "Unknown",    year: 1998, confidence: "medium" },
  { id: 26,  name: "Chrysanthemum 'Feeling Green'", aka: "Feeling Green",         zhName: "绿意菊",      category: "Chrysanthemum", tags: ["green","novelty","cut flower","trending","unique"],                        score: 85, trend: "+6.2", trendDir: "up",     mentions: 19700, pos: 72, neu: 20, neg: 8,  region: "Global",        season: "Autumn",        breeder: "Deliflor",   year: 2010, confidence: "medium" },
  { id: 27,  name: "Chrysanthemum 'Baltica'",    aka: "Baltica",                  zhName: "波罗的海菊",  category: "Chrysanthemum", tags: ["white","standard","cut flower","reliable","florist"],                      score: 77, trend: "+0.8", trendDir: "up",     mentions: 14200, pos: 62, neu: 26, neg: 12, region: "Europe",        season: "Autumn",        breeder: "Fides",      year: 1988, confidence: "medium" },
  { id: 28,  name: "Chrysanthemum 'Puma'",       aka: "Puma",                     zhName: "美洲豹菊",    category: "Chrysanthemum", tags: ["spray","pink","garden","compact","hardy"],                                  score: 74, trend: "+1.0", trendDir: "up",     mentions: 11600, pos: 60, neu: 28, neg: 12, region: "Europe",        season: "Autumn",        breeder: "Yoder",      year: 2005, confidence: "low" },

  // ============================================================
  // LAVENDER — 薰衣草
  // ============================================================
  { id: 29,  name: "Lavender 'Hidcote'",         aka: "Hidcote Blue",             zhName: "希德寇特薰衣草", category: "Lavender",   tags: ["compact","dark purple","fragrant","award","garden","hedge","RHS"],         score: 91, trend: "+3.1", trendDir: "up",     mentions: 42100, pos: 78, neu: 15, neg: 7,  region: "Europe",        season: "Summer",        breeder: "Unknown",    year: 1950, confidence: "high" },
  { id: 30,  name: "Lavender 'Grosso'",          aka: "Fat Spike",                zhName: "格罗索薰衣草", category: "Lavender",    tags: ["large spike","fragrant","commercial","essential oil","drought tolerant"],   score: 86, trend: "+2.5", trendDir: "up",     mentions: 29800, pos: 73, neu: 18, neg: 9,  region: "Europe",        season: "Summer",        breeder: "Upson",      year: 1972, confidence: "high" },
  { id: 31,  name: "Lavender 'Munstead'",        aka: "Munstead Lavender",        zhName: "芒斯特德薰衣草", category: "Lavender",   tags: ["compact","blue purple","fragrant","hardy","traditional","cottage"],         score: 83, trend: "+1.8", trendDir: "up",     mentions: 24600, pos: 69, neu: 22, neg: 9,  region: "Global",        season: "Summer",        breeder: "Gertrude Jekyll", year: 1916, confidence: "high" },
  { id: 32,  name: "Lavender 'Phenomenal'",      aka: "Phenomenal Lavender",      zhName: "现象薰衣草",   category: "Lavender",    tags: ["heat tolerant","humid","disease resistant","large","American"],             score: 88, trend: "+4.7", trendDir: "up",     mentions: 18900, pos: 76, neu: 17, neg: 7,  region: "North America", season: "Summer",        breeder: "Peace Tree Farm", year: 2012, confidence: "medium" },
  { id: 33,  name: "Lavender 'Vera'",            aka: "True Lavender",            zhName: "真正薰衣草",   category: "Lavender",    tags: ["traditional","fragrant","essential oil","Provence","classic"],              score: 80, trend: "+0.6", trendDir: "up",     mentions: 16300, pos: 65, neu: 25, neg: 10, region: "Europe",        season: "Summer",        breeder: "Traditional",year: 1900, confidence: "medium" },
  { id: 34,  name: "Lavender 'Edelweiss'",       aka: "White Lavender",           zhName: "白色薰衣草",   category: "Lavender",    tags: ["white","unusual","fragrant","compact","novelty"],                           score: 75, trend: "+1.3", trendDir: "up",     mentions: 9800,  pos: 61, neu: 27, neg: 12, region: "Europe",        season: "Summer",        breeder: "Unknown",    year: 1995, confidence: "low" },

  // ============================================================
  // HYDRANGEA — 绣球花
  // ============================================================
  { id: 35,  name: "Hydrangea 'Annabelle'",      aka: "Smooth Hydrangea Annabelle", zhName: "安娜贝尔绣球", category: "Hydrangea",  tags: ["white","large bloom","hardy","shade tolerant","classic","award"],          score: 88, trend: "+5.2", trendDir: "up",     mentions: 38700, pos: 75, neu: 17, neg: 8,  region: "Global",        season: "Summer",        breeder: "Wild selection", year: 1960, confidence: "high" },
  { id: 36,  name: "Hydrangea 'Incrediball'",    aka: "Incrediball Hydrangea",    zhName: "超级球绣球",   category: "Hydrangea",   tags: ["giant bloom","white","strong stems","improved annabelle","award"],          score: 72, trend: "+11.4",trendDir: "up",     mentions: 8200,  pos: 60, neu: 28, neg: 12, region: "North America", season: "Summer",        breeder: "Proven Winners", year: 2010, confidence: "medium" },
  { id: 37,  name: "Hydrangea 'Limelight'",      aka: "Limelight Hydrangea",      zhName: "石灰光绣球",   category: "Hydrangea",   tags: ["lime green","white","panicle","award","popular","easy care"],               score: 90, trend: "+4.8", trendDir: "up",     mentions: 44200, pos: 77, neu: 16, neg: 7,  region: "North America", season: "Summer/Autumn", breeder: "Dirr",       year: 2002, confidence: "high" },
  { id: 38,  name: "Hydrangea 'Endless Summer'", aka: "Endless Summer",           zhName: "无尽夏绣球",   category: "Hydrangea",   tags: ["reblooming","blue pink","mophead","award","popular","repeat bloom"],        score: 87, trend: "+3.9", trendDir: "up",     mentions: 39800, pos: 74, neu: 18, neg: 8,  region: "Global",        season: "Summer/Autumn", breeder: "Bailey Nurseries", year: 2004, confidence: "high" },
  { id: 39,  name: "Hydrangea 'Pinky Winky'",    aka: "Pinky Winky",              zhName: "粉红温基绣球", category: "Hydrangea",   tags: ["bicolor","pink white","panicle","award","unique"],                          score: 83, trend: "+2.7", trendDir: "up",     mentions: 21400, pos: 69, neu: 22, neg: 9,  region: "Europe",        season: "Summer/Autumn", breeder: "Dirr",       year: 2003, confidence: "medium" },
  { id: 40,  name: "Hydrangea 'Little Quick Fire'", aka: "Little Quick Fire",     zhName: "小快火绣球",   category: "Hydrangea",   tags: ["compact","early bloom","white pink","panicle","small garden"],              score: 79, trend: "+2.1", trendDir: "up",     mentions: 14600, pos: 64, neu: 25, neg: 11, region: "North America", season: "Summer",        breeder: "Proven Winners", year: 2010, confidence: "medium" },
  { id: 41,  name: "Hydrangea 'Nikko Blue'",     aka: "Nikko Blue",               zhName: "日光蓝绣球",   category: "Hydrangea",   tags: ["blue","mophead","classic","shade","popular"],                               score: 81, trend: "+1.3", trendDir: "up",     mentions: 18900, pos: 67, neu: 23, neg: 10, region: "North America", season: "Summer",        breeder: "Unknown",    year: 1960, confidence: "high" },

  // ============================================================
  // TULIP — 郁金香
  // ============================================================
  { id: 42,  name: "Tulip 'Apeldoorn'",          aka: "Darwin Hybrid Apeldoorn",  zhName: "阿珀尔多伦郁金香", category: "Tulip",    tags: ["red","darwin hybrid","large","classic","cut flower","Netherlands"],        score: 76, trend: "-0.8", trendDir: "down",   mentions: 22300, pos: 61, neu: 26, neg: 13, region: "Netherlands",   season: "Spring",        breeder: "Lefeber",    year: 1951, confidence: "high" },
  { id: 43,  name: "Tulip 'Queen of Night'",     aka: "Queen of Night Tulip",     zhName: "黑夜女王郁金香", category: "Tulip",    tags: ["dark purple","almost black","dramatic","cut flower","unique","popular"],    score: 88, trend: "+4.6", trendDir: "up",     mentions: 31200, pos: 75, neu: 18, neg: 7,  region: "Global",        season: "Spring",        breeder: "Segers",     year: 1944, confidence: "high" },
  { id: 44,  name: "Tulip 'Angelique'",          aka: "Angelique Peony Tulip",    zhName: "天使绒郁金香",  category: "Tulip",     tags: ["peony-flowered","pale pink","fragrant","romantic","popular"],               score: 85, trend: "+3.2", trendDir: "up",     mentions: 24800, pos: 72, neu: 20, neg: 8,  region: "Global",        season: "Spring",        breeder: "Unknown",    year: 1959, confidence: "high" },
  { id: 45,  name: "Tulip 'Ballerina'",          aka: "Ballerina Tulip",          zhName: "芭蕾舞者郁金香", category: "Tulip",    tags: ["lily-flowered","orange","fragrant","elegant","award"],                      score: 83, trend: "+2.0", trendDir: "up",     mentions: 18700, pos: 69, neu: 22, neg: 9,  region: "Europe",        season: "Spring",        breeder: "Unknown",    year: 1980, confidence: "medium" },
  { id: 46,  name: "Tulip 'Parrot King'",        aka: "Parrot King",              zhName: "鹦鹉王郁金香", category: "Tulip",     tags: ["parrot","red","fringed","dramatic","show","exhibition"],                    score: 77, trend: "+1.1", trendDir: "up",     mentions: 11400, pos: 63, neu: 25, neg: 12, region: "Netherlands",   season: "Spring",        breeder: "Unknown",    year: 1970, confidence: "medium" },
  { id: 47,  name: "Tulip 'Purple Rain'",        aka: "Purple Rain",              zhName: "紫雨郁金香",    category: "Tulip",    tags: ["purple","viridiflora","green stripe","unique","novelty"],                   score: 74, trend: "+0.8", trendDir: "up",     mentions: 9600,  pos: 60, neu: 28, neg: 12, region: "Netherlands",   season: "Spring",        breeder: "Unknown",    year: 1990, confidence: "low" },
  { id: 48,  name: "Tulip 'White Triumphator'",  aka: "White Triumphator",        zhName: "白色凯旋郁金香", category: "Tulip",    tags: ["lily-flowered","white","elegant","pure","wedding"],                         score: 82, trend: "+1.7", trendDir: "up",     mentions: 15300, pos: 68, neu: 23, neg: 9,  region: "Global",        season: "Spring",        breeder: "Unknown",    year: 1942, confidence: "medium" },

  // ============================================================
  // ORCHID — 兰花
  // ============================================================
  { id: 49,  name: "Orchid 'Phalaenopsis Cascade'", aka: "Cascade Phalaenopsis", zhName: "瀑布蝴蝶兰",   category: "Orchid",      tags: ["phalaenopsis","cascading","white","popular","indoor","long lasting"],       score: 83, trend: "+1.9", trendDir: "up",     mentions: 31200, pos: 68, neu: 22, neg: 10, region: "Asia",          season: "Winter/Spring", breeder: "Various",    year: 2000, confidence: "high" },
  { id: 50,  name: "Orchid 'Dendrobium Nobile'", aka: "Noble Orchid",            zhName: "石斛兰",       category: "Orchid",       tags: ["dendrobium","fragrant","purple white","traditional","Chinese medicine"],    score: 79, trend: "+1.2", trendDir: "up",     mentions: 22400, pos: 64, neu: 25, neg: 11, region: "Asia",          season: "Spring",        breeder: "Traditional",year: 1800, confidence: "medium" },
  { id: 51,  name: "Orchid 'Cymbidium Showgirl'", aka: "Showgirl Cymbidium",     zhName: "秀女大花蕙兰", category: "Orchid",       tags: ["cymbidium","pink","large bloom","show","exhibition","Chinese New Year"],   score: 85, trend: "+3.8", trendDir: "up",     mentions: 28700, pos: 72, neu: 20, neg: 8,  region: "Asia",          season: "Winter/Spring", breeder: "Various",    year: 1990, confidence: "medium" },
  { id: 52,  name: "Orchid 'Cattleya Trianae'",  aka: "Christmas Orchid",        zhName: "圣诞卡特兰",   category: "Orchid",       tags: ["cattleya","fragrant","purple","Christmas","classic","show"],                score: 81, trend: "+1.5", trendDir: "up",     mentions: 14600, pos: 67, neu: 23, neg: 10, region: "Global",        season: "Winter",        breeder: "Colombia",   year: 1860, confidence: "medium" },
  { id: 53,  name: "Orchid 'Vanda Blue Magic'",  aka: "Blue Vanda",              zhName: "蓝色万代兰",   category: "Orchid",       tags: ["vanda","blue","rare","tropical","show","dramatic"],                         score: 87, trend: "+5.3", trendDir: "up",     mentions: 19800, pos: 74, neu: 18, neg: 8,  region: "Asia",          season: "Summer",        breeder: "Various",    year: 1980, confidence: "medium" },

  // ============================================================
  // PETUNIA — 矮牵牛
  // ============================================================
  { id: 54,  name: "Petunia 'Supertunia Vista'", aka: "Supertunia Vista Bubblegum", zhName: "超级矮牵牛", category: "Petunia",    tags: ["spreading","pink","prolific","container","heat tolerant","award"],          score: 79, trend: "+1.5", trendDir: "up",     mentions: 19800, pos: 63, neu: 24, neg: 13, region: "Global",        season: "Summer",        breeder: "Proven Winners", year: 2005, confidence: "high" },
  { id: 55,  name: "Petunia 'Wave Purple'",      aka: "Purple Wave",              zhName: "紫色波浪矮牵牛", category: "Petunia",  tags: ["spreading","purple","ground cover","award","popular"],                      score: 74, trend: "-1.4", trendDir: "down",   mentions: 15600, pos: 59, neu: 28, neg: 13, region: "North America", season: "Summer",        breeder: "PanAmerican Seed", year: 1995, confidence: "high" },
  { id: 56,  name: "Petunia 'Tidal Wave'",       aka: "Tidal Wave Red Velour",    zhName: "海浪矮牵牛",   category: "Petunia",     tags: ["vigorous","red","spreading","hedgiflora","large"],                          score: 77, trend: "+0.9", trendDir: "up",     mentions: 12400, pos: 62, neu: 26, neg: 12, region: "North America", season: "Summer",        breeder: "PanAmerican Seed", year: 2003, confidence: "medium" },
  { id: 57,  name: "Petunia 'Phantom'",          aka: "Phantom Petunia",          zhName: "幻影矮牵牛",   category: "Petunia",     tags: ["yellow black","bicolor","novelty","dramatic","unique","trending"],           score: 82, trend: "+5.1", trendDir: "up",     mentions: 17800, pos: 68, neu: 22, neg: 10, region: "Global",        season: "Summer",        breeder: "Syngenta",   year: 2012, confidence: "medium" },
  { id: 58,  name: "Petunia 'Sophistica'",       aka: "Sophistica Lime Bicolor",  zhName: "优雅矮牵牛",   category: "Petunia",     tags: ["lime green","bicolor","novelty","container","unique"],                      score: 76, trend: "+1.8", trendDir: "up",     mentions: 10200, pos: 61, neu: 27, neg: 12, region: "Global",        season: "Summer",        breeder: "Syngenta",   year: 2015, confidence: "low" },

  // ============================================================
  // DAHLIA — 大丽花
  // ============================================================
  { id: 59,  name: "Dahlia 'Café au Lait'",      aka: "Cafe au Lait Dahlia",      zhName: "咖啡拿铁大丽花", category: "Dahlia",    tags: ["blush","cream","peach","wedding","popular","Instagram","trending"],         score: 68, trend: "+7.2", trendDir: "up",     mentions: 7800,  pos: 57, neu: 30, neg: 13, region: "Global",        season: "Summer/Autumn", breeder: "Unknown",    year: 1990, confidence: "medium" },
  { id: 60,  name: "Dahlia 'Bishop of Llandaff'", aka: "Bishop of Llandaff",     zhName: "兰达夫主教大丽花", category: "Dahlia",  tags: ["red","dark foliage","award","dramatic","RHS","peony-flowered"],             score: 85, trend: "+3.4", trendDir: "up",     mentions: 21300, pos: 71, neu: 21, neg: 8,  region: "Europe",        season: "Summer/Autumn", breeder: "Treseder",   year: 1928, confidence: "high" },
  { id: 61,  name: "Dahlia 'Karma Choc'",        aka: "Karma Choc",               zhName: "巧克力因果大丽花", category: "Dahlia",  tags: ["dark chocolate","deep red","cut flower","florist","award"],                 score: 83, trend: "+2.8", trendDir: "up",     mentions: 18700, pos: 69, neu: 22, neg: 9,  region: "Europe",        season: "Summer/Autumn", breeder: "Westland",   year: 2002, confidence: "medium" },
  { id: 62,  name: "Dahlia 'Mystic Illusion'",   aka: "Mystic Illusion",          zhName: "神秘幻觉大丽花", category: "Dahlia",    tags: ["yellow","dark foliage","single","compact","garden","award"],               score: 80, trend: "+2.2", trendDir: "up",     mentions: 14200, pos: 66, neu: 24, neg: 10, region: "North America", season: "Summer/Autumn", breeder: "Unwins",     year: 2007, confidence: "medium" },
  { id: 63,  name: "Dahlia 'Thomas Edison'",     aka: "Thomas Edison Dahlia",     zhName: "爱迪生大丽花",  category: "Dahlia",     tags: ["purple","large","dinner plate","classic","show"],                           score: 77, trend: "+0.6", trendDir: "up",     mentions: 11800, pos: 62, neu: 26, neg: 12, region: "North America", season: "Summer/Autumn", breeder: "Unknown",    year: 1929, confidence: "medium" },

  // ============================================================
  // LILY — 百合
  // ============================================================
  { id: 64,  name: "Lilium 'Stargazer'",         aka: "Stargazer Lily",           zhName: "星光百合",    category: "Lily",         tags: ["oriental","pink","fragrant","popular","cut flower","award"],               score: 89, trend: "+4.1", trendDir: "up",     mentions: 36400, pos: 76, neu: 17, neg: 7,  region: "Global",        season: "Summer",        breeder: "Woodriff",   year: 1978, confidence: "high" },
  { id: 65,  name: "Lilium 'Casa Blanca'",       aka: "Casa Blanca Lily",         zhName: "卡萨布兰卡百合", category: "Lily",      tags: ["oriental","white","fragrant","wedding","classic","cut flower"],             score: 87, trend: "+3.5", trendDir: "up",     mentions: 28900, pos: 74, neu: 19, neg: 7,  region: "Global",        season: "Summer",        breeder: "Unknown",    year: 1986, confidence: "high" },
  { id: 66,  name: "Lilium 'Conca d'Or'",        aka: "Conca d'Or",               zhName: "黄金湾百合",   category: "Lily",         tags: ["orienpet","yellow","fragrant","large","award","hybrid"],                    score: 84, trend: "+2.9", trendDir: "up",     mentions: 16700, pos: 70, neu: 22, neg: 8,  region: "Europe",        season: "Summer",        breeder: "van den Berg", year: 1988, confidence: "medium" },
  { id: 67,  name: "Lilium 'Tiny Bee'",          aka: "Tiny Bee",                 zhName: "小蜜蜂百合",   category: "Lily",         tags: ["asiatic","yellow","compact","patio","container","dwarf"],                   score: 76, trend: "+1.4", trendDir: "up",     mentions: 9800,  pos: 62, neu: 26, neg: 12, region: "North America", season: "Summer",        breeder: "Vletter",    year: 2010, confidence: "low" },
  { id: 68,  name: "Lilium 'Black Beauty'",      aka: "Black Beauty Lily",        zhName: "黑美人百合",   category: "Lily",         tags: ["orienpet","dark red","fragrant","tall","dramatic","award"],                 score: 82, trend: "+2.1", trendDir: "up",     mentions: 14300, pos: 68, neu: 23, neg: 9,  region: "Global",        season: "Summer",        breeder: "Woodriff",   year: 1957, confidence: "medium" },

  // ============================================================
  // PEONY — 牡丹 / 芍药
  // ============================================================
  { id: 69,  name: "Paeonia 'Sarah Bernhardt'",  aka: "Sarah Bernhardt Peony",    zhName: "莎拉·伯恩哈特芍药", category: "Peony",  tags: ["pink","fragrant","classic","cut flower","award","popular"],                score: 90, trend: "+4.3", trendDir: "up",     mentions: 38600, pos: 77, neu: 16, neg: 7,  region: "Global",        season: "Spring/Summer", breeder: "Lemoine",    year: 1906, confidence: "high" },
  { id: 70,  name: "Paeonia 'Coral Charm'",      aka: "Coral Charm",              zhName: "珊瑚魅力芍药", category: "Peony",       tags: ["coral","color changing","award","popular","cut flower"],                    score: 88, trend: "+5.0", trendDir: "up",     mentions: 29400, pos: 75, neu: 18, neg: 7,  region: "North America", season: "Spring/Summer", breeder: "Wissing",    year: 1964, confidence: "high" },
  { id: 71,  name: "Paeonia 'Bowl of Beauty'",   aka: "Bowl of Beauty",           zhName: "美丽碗芍药",   category: "Peony",        tags: ["anemone","pink white","classic","award","popular"],                         score: 85, trend: "+2.8", trendDir: "up",     mentions: 21800, pos: 71, neu: 21, neg: 8,  region: "Europe",        season: "Spring/Summer", breeder: "Hoogendoorn", year: 1949, confidence: "high" },
  { id: 72,  name: "Paeonia 'Karl Rosenfield'",  aka: "Karl Rosenfield",          zhName: "卡尔·罗森菲尔德芍药", category: "Peony", tags: ["deep red","fragrant","classic","cut flower","reliable"],                  score: 82, trend: "+1.6", trendDir: "up",     mentions: 16400, pos: 68, neu: 23, neg: 9,  region: "North America", season: "Spring/Summer", breeder: "Rosenfield", year: 1908, confidence: "medium" },
  { id: 73,  name: "Paeonia suffruticosa 'Luo Yang Hong'", aka: "Luoyang Red",    zhName: "洛阳红牡丹",   category: "Peony",        tags: ["tree peony","red","Chinese","traditional","Luoyang","heritage"],            score: 86, trend: "+3.9", trendDir: "up",     mentions: 24700, pos: 73, neu: 19, neg: 8,  region: "China",         season: "Spring",        breeder: "China traditional", year: 1800, confidence: "medium" },
  { id: 74,  name: "Paeonia suffruticosa 'Zhao Fen'", aka: "Zhao Fen",           zhName: "赵粉牡丹",     category: "Peony",        tags: ["tree peony","pink","Chinese","traditional","heritage","popular"],            score: 84, trend: "+3.2", trendDir: "up",     mentions: 19800, pos: 70, neu: 22, neg: 8,  region: "China",         season: "Spring",        breeder: "China traditional", year: 1700, confidence: "medium" },

  // ============================================================
  // ECHINACEA / PERENNIAL — 松果菊 / 宿根花卉
  // ============================================================
  { id: 75,  name: "Echinacea 'Magnus'",         aka: "Magnus Purple Coneflower", zhName: "马格纳斯松果菊", category: "Perennial",  tags: ["purple","award","pollinator","prairie","hardy","RHS","Perennial Plant of the Year"], score: 75, trend: "+8.7", trendDir: "up", mentions: 11300, pos: 62, neu: 26, neg: 12, region: "North America", season: "Summer/Autumn", breeder: "Magnus Nilsson", year: 1998, confidence: "medium" },
  { id: 76,  name: "Echinacea 'PowWow Wild Berry'", aka: "PowWow Wild Berry",     zhName: "野莓松果菊",   category: "Perennial",    tags: ["rose pink","compact","award","pollinator","long blooming"],                 score: 79, trend: "+3.4", trendDir: "up",     mentions: 8900,  pos: 64, neu: 25, neg: 11, region: "North America", season: "Summer/Autumn", breeder: "Benary",     year: 2010, confidence: "medium" },
  { id: 77,  name: "Salvia 'Caradonna'",         aka: "Caradonna Salvia",         zhName: "卡拉多纳鼠尾草", category: "Perennial",  tags: ["purple","dark stem","pollinator","award","drought tolerant","RHS"],         score: 71, trend: "+7.9", trendDir: "up",     mentions: 9400,  pos: 59, neu: 29, neg: 12, region: "Europe",        season: "Summer",        breeder: "Unknown",    year: 1996, confidence: "medium" },
  { id: 78,  name: "Rudbeckia 'Goldsturm'",      aka: "Black-eyed Susan Goldsturm", zhName: "金风暴黑心菊", category: "Perennial",  tags: ["yellow","black center","award","pollinator","hardy","Perennial Plant of the Year"], score: 80, trend: "+2.3", trendDir: "up", mentions: 16800, pos: 66, neu: 24, neg: 10, region: "North America", season: "Summer/Autumn", breeder: "Kayser",     year: 1937, confidence: "high" },
  { id: 79,  name: "Agapanthus 'Midnight Blue'", aka: "Midnight Blue Agapanthus", zhName: "午夜蓝百子莲", category: "Perennial",    tags: ["deep blue","compact","drought tolerant","award","Mediterranean"],           score: 82, trend: "+3.1", trendDir: "up",     mentions: 12400, pos: 68, neu: 23, neg: 9,  region: "Europe",        season: "Summer",        breeder: "Various",    year: 2000, confidence: "medium" },

  // ============================================================
  // GERANIUM / PELARGONIUM — 天竺葵
  // ============================================================
  { id: 80,  name: "Geranium 'Maverick Red'",    aka: "Maverick Red Geranium",    zhName: "红色独行侠天竺葵", category: "Geranium",  tags: ["red","zonal","popular","bedding","container"],                              score: 65, trend: "-2.7", trendDir: "down",   mentions: 9800,  pos: 52, neu: 31, neg: 17, region: "North America", season: "Summer",        breeder: "Ball Seed",  year: 1990, confidence: "medium" },
  { id: 81,  name: "Pelargonium 'Caliente Fire'", aka: "Caliente Fire",           zhName: "火焰天竺葵",   category: "Geranium",     tags: ["orange red","heat tolerant","ivy","trailing","container","award"],           score: 78, trend: "+2.4", trendDir: "up",     mentions: 11200, pos: 63, neu: 26, neg: 11, region: "Global",        season: "Summer",        breeder: "Dümmen Orange", year: 2008, confidence: "medium" },
  { id: 82,  name: "Pelargonium 'Pac Idols'",    aka: "Pac Idols",                zhName: "偶像天竺葵",   category: "Geranium",     tags: ["bicolor","white pink","unique","container","novelty"],                      score: 72, trend: "+1.1", trendDir: "up",     mentions: 7600,  pos: 58, neu: 29, neg: 13, region: "Europe",        season: "Summer",        breeder: "Selecta",    year: 2012, confidence: "low" },

  // ============================================================
  // IMPATIENS — 凤仙花
  // ============================================================
  { id: 83,  name: "Impatiens 'SunPatiens Compact'", aka: "SunPatiens",           zhName: "阳光凤仙花",   category: "Impatiens",    tags: ["sun tolerant","heat tolerant","vigorous","award","disease resistant"],      score: 84, trend: "+4.2", trendDir: "up",     mentions: 22600, pos: 70, neu: 22, neg: 8,  region: "North America", season: "Summer",        breeder: "Sakata",     year: 2006, confidence: "high" },
  { id: 84,  name: "Impatiens 'Beacon'",         aka: "Beacon Impatiens",         zhName: "灯塔凤仙花",   category: "Impatiens",    tags: ["downy mildew resistant","shade","bedding","reliable","award"],              score: 80, trend: "+3.1", trendDir: "up",     mentions: 16800, pos: 66, neu: 24, neg: 10, region: "North America", season: "Summer",        breeder: "PanAmerican Seed", year: 2018, confidence: "medium" },

  // ============================================================
  // BEGONIA — 秋海棠
  // ============================================================
  { id: 85,  name: "Begonia 'Dragon Wing'",      aka: "Dragon Wing Begonia",      zhName: "龙翼秋海棠",   category: "Begonia",      tags: ["red","large","heat tolerant","sun tolerant","container","popular"],         score: 82, trend: "+2.8", trendDir: "up",     mentions: 18400, pos: 68, neu: 23, neg: 9,  region: "North America", season: "Summer",        breeder: "Benary",     year: 2000, confidence: "high" },
  { id: 86,  name: "Begonia 'Nonstop'",          aka: "Nonstop Tuberous Begonia", zhName: "不停歇球根秋海棠", category: "Begonia",   tags: ["tuberous","double","prolific","shade","container","award"],                 score: 79, trend: "+1.5", trendDir: "up",     mentions: 14200, pos: 64, neu: 25, neg: 11, region: "Europe",        season: "Summer",        breeder: "Benary",     year: 1975, confidence: "medium" },

  // ============================================================
  // MARIGOLD — 万寿菊
  // ============================================================
  { id: 87,  name: "Tagetes 'Vanilla'",          aka: "Vanilla Marigold",         zhName: "香草万寿菊",   category: "Marigold",     tags: ["cream white","unique","award","unusual","novelty","All-America Selections"], score: 77, trend: "+2.1", trendDir: "up",    mentions: 12800, pos: 62, neu: 27, neg: 11, region: "North America", season: "Summer",        breeder: "Hem Genetics", year: 2005, confidence: "medium" },
  { id: 88,  name: "Tagetes 'Bonanza Flame'",    aka: "Bonanza Flame",            zhName: "火焰万寿菊",   category: "Marigold",     tags: ["orange red","bicolor","french","compact","bedding","award"],                score: 74, trend: "+0.9", trendDir: "up",     mentions: 9600,  pos: 60, neu: 28, neg: 12, region: "North America", season: "Summer",        breeder: "PanAmerican Seed", year: 1990, confidence: "medium" },

  // ============================================================
  // SUNFLOWER — 向日葵
  // ============================================================
  { id: 89,  name: "Helianthus 'Sunrich Orange'", aka: "Sunrich Orange",          zhName: "橙色阳光向日葵", category: "Sunflower",  tags: ["pollenless","cut flower","orange","commercial","florist"],                  score: 83, trend: "+3.2", trendDir: "up",     mentions: 21400, pos: 69, neu: 22, neg: 9,  region: "Global",        season: "Summer",        breeder: "Sakata",     year: 1998, confidence: "high" },
  { id: 90,  name: "Helianthus 'Teddy Bear'",    aka: "Teddy Bear Sunflower",     zhName: "泰迪熊向日葵",  category: "Sunflower",   tags: ["double","fluffy","compact","cute","garden","popular"],                      score: 80, trend: "+2.6", trendDir: "up",     mentions: 17800, pos: 67, neu: 24, neg: 9,  region: "Global",        season: "Summer",        breeder: "Unknown",    year: 1985, confidence: "medium" },
  { id: 91,  name: "Helianthus 'Moulin Rouge'",  aka: "Moulin Rouge Sunflower",   zhName: "红磨坊向日葵",  category: "Sunflower",   tags: ["dark red","pollenless","cut flower","dramatic","unique"],                   score: 78, trend: "+1.8", trendDir: "up",     mentions: 13200, pos: 63, neu: 26, neg: 11, region: "Global",        season: "Summer",        breeder: "Syngenta",   year: 2002, confidence: "medium" },

  // ============================================================
  // ZINNIA — 百日草
  // ============================================================
  { id: 92,  name: "Zinnia 'Benary's Giant'",    aka: "Benary's Giant Zinnia",    zhName: "贝纳里巨型百日草", category: "Zinnia",    tags: ["large","cut flower","prolific","heat tolerant","award","popular"],          score: 85, trend: "+4.0", trendDir: "up",     mentions: 24600, pos: 71, neu: 21, neg: 8,  region: "North America", season: "Summer",        breeder: "Benary",     year: 1990, confidence: "high" },
  { id: 93,  name: "Zinnia 'Queen Red Lime'",    aka: "Queen Red Lime",           zhName: "红绿女王百日草", category: "Zinnia",     tags: ["bicolor","red lime","unique","cut flower","trending","Instagram"],           score: 82, trend: "+5.8", trendDir: "up",     mentions: 18900, pos: 68, neu: 23, neg: 9,  region: "Global",        season: "Summer",        breeder: "Unknown",    year: 2008, confidence: "medium" },

  // ============================================================
  // SNAPDRAGON — 金鱼草
  // ============================================================
  { id: 94,  name: "Antirrhinum 'Chantilly'",    aka: "Chantilly Snapdragon",     zhName: "尚蒂伊金鱼草", category: "Snapdragon",   tags: ["open-faced","cut flower","fragrant","florist","popular"],                   score: 80, trend: "+2.4", trendDir: "up",     mentions: 14800, pos: 65, neu: 26, neg: 9,  region: "Global",        season: "Spring/Autumn", breeder: "Sakata",     year: 1995, confidence: "medium" },
  { id: 95,  name: "Antirrhinum 'Rocket'",       aka: "Rocket Snapdragon",        zhName: "火箭金鱼草",   category: "Snapdragon",   tags: ["tall","cut flower","classic","reliable","commercial"],                      score: 76, trend: "+0.8", trendDir: "up",     mentions: 10400, pos: 61, neu: 27, neg: 12, region: "North America", season: "Spring/Autumn", breeder: "PanAmerican Seed", year: 1975, confidence: "medium" },

  // ============================================================
  // CARNATION — 康乃馨
  // ============================================================
  { id: 96,  name: "Dianthus 'Prado'",           aka: "Prado Carnation",          zhName: "普拉多康乃馨", category: "Carnation",    tags: ["green","unique","florist","novelty","cut flower"],                          score: 79, trend: "+2.9", trendDir: "up",     mentions: 13600, pos: 64, neu: 25, neg: 11, region: "Europe",        season: "Year-round",    breeder: "Barberet & Blanc", year: 2000, confidence: "medium" },
  { id: 97,  name: "Dianthus 'Moonique'",        aka: "Moonique",                 zhName: "月光康乃馨",   category: "Carnation",    tags: ["white","fragrant","classic","cut flower","wedding","Mother's Day"],          score: 82, trend: "+1.7", trendDir: "up",     mentions: 19800, pos: 67, neu: 24, neg: 9,  region: "Global",        season: "Year-round",    breeder: "Barberet & Blanc", year: 2005, confidence: "medium" },

  // ============================================================
  // GERBERA — 非洲菊
  // ============================================================
  { id: 98,  name: "Gerbera 'Revolution'",       aka: "Revolution Gerbera",       zhName: "革命非洲菊",   category: "Gerbera",      tags: ["large","cut flower","prolific","heat tolerant","popular"],                  score: 81, trend: "+2.3", trendDir: "up",     mentions: 16400, pos: 67, neu: 24, neg: 9,  region: "Global",        season: "Year-round",    breeder: "Florist Holland", year: 2000, confidence: "medium" },
  { id: 99,  name: "Gerbera 'Garvinea'",         aka: "Garvinea Sweet Glow",      zhName: "加维尼亚非洲菊", category: "Gerbera",    tags: ["garden","hardy","long blooming","award","compact"],                         score: 78, trend: "+3.1", trendDir: "up",     mentions: 11800, pos: 63, neu: 26, neg: 11, region: "Europe",        season: "Spring/Autumn", breeder: "Florist Holland", year: 2010, confidence: "medium" },

  // ============================================================
  // LISIANTHUS — 洋桔梗
  // ============================================================
  { id: 100, name: "Eustoma 'Voyage'",           aka: "Voyage Lisianthus",        zhName: "航行洋桔梗",   category: "Lisianthus",   tags: ["cut flower","double","popular","florist","wedding","long vase life"],       score: 85, trend: "+3.8", trendDir: "up",     mentions: 18200, pos: 71, neu: 21, neg: 8,  region: "Asia",          season: "Summer",        breeder: "Sakata",     year: 2000, confidence: "medium" },
  { id: 101, name: "Eustoma 'Echo'",             aka: "Echo Lisianthus",          zhName: "回声洋桔梗",   category: "Lisianthus",   tags: ["cut flower","double","prolific","award","florist"],                          score: 82, trend: "+2.6", trendDir: "up",     mentions: 14600, pos: 68, neu: 23, neg: 9,  region: "Global",        season: "Summer",        breeder: "Sakata",     year: 1995, confidence: "medium" },

  // ============================================================
  // ANEMONE — 银莲花
  // ============================================================
  { id: 102, name: "Anemone 'Meron'",            aka: "Meron Anemone",            zhName: "梅隆银莲花",   category: "Anemone",      tags: ["cut flower","blue","popular","florist","spring"],                            score: 80, trend: "+2.1", trendDir: "up",     mentions: 12800, pos: 65, neu: 25, neg: 10, region: "Europe",        season: "Spring",        breeder: "Anemone growers", year: 1990, confidence: "medium" },
  { id: 103, name: "Anemone 'Galilee'",          aka: "Galilee Anemone",          zhName: "加利利银莲花", category: "Anemone",       tags: ["mixed colors","cut flower","florist","Israeli","popular"],                   score: 77, trend: "+1.4", trendDir: "up",     mentions: 9400,  pos: 62, neu: 27, neg: 11, region: "Europe",        season: "Spring",        breeder: "Israel",     year: 1985, confidence: "low" },

  // ============================================================
  // RANUNCULUS — 毛茛 / 花毛茛
  // ============================================================
  { id: 104, name: "Ranunculus 'Cloni Success'", aka: "Cloni Ranunculus",         zhName: "克隆尼花毛茛", category: "Ranunculus",   tags: ["double","pastel","popular","florist","wedding","cut flower","trending"],    score: 88, trend: "+6.4", trendDir: "up",     mentions: 24800, pos: 75, neu: 18, neg: 7,  region: "Global",        season: "Spring",        breeder: "Ercole Ramazzotti", year: 2005, confidence: "high" },
  { id: 105, name: "Ranunculus 'Elegance'",      aka: "Elegance Ranunculus",      zhName: "优雅花毛茛",   category: "Ranunculus",   tags: ["double","mixed","cut flower","florist","spring"],                            score: 83, trend: "+3.2", trendDir: "up",     mentions: 16400, pos: 69, neu: 22, neg: 9,  region: "Europe",        season: "Spring",        breeder: "Various",    year: 2000, confidence: "medium" },

  // ============================================================
  // SWEET PEA — 香豌豆
  // ============================================================
  { id: 106, name: "Lathyrus 'Spencer'",         aka: "Spencer Sweet Pea",        zhName: "斯宾塞香豌豆", category: "Sweet Pea",    tags: ["fragrant","ruffled","cut flower","classic","award","heritage"],             score: 86, trend: "+3.7", trendDir: "up",     mentions: 19800, pos: 73, neu: 19, neg: 8,  region: "Europe",        season: "Spring",        breeder: "Silas Cole",  year: 1901, confidence: "high" },
  { id: 107, name: "Lathyrus 'Matucana'",        aka: "Matucana Sweet Pea",       zhName: "马图卡纳香豌豆", category: "Sweet Pea",  tags: ["bicolor","fragrant","heritage","intense scent","purple red"],               score: 84, trend: "+2.9", trendDir: "up",     mentions: 14200, pos: 70, neu: 22, neg: 8,  region: "Europe",        season: "Spring",        breeder: "Peru origin", year: 1900, confidence: "medium" },

  // ============================================================
  // COSMOS — 波斯菊
  // ============================================================
  { id: 108, name: "Cosmos 'Purity'",            aka: "Purity Cosmos",            zhName: "纯洁波斯菊",   category: "Cosmos",       tags: ["white","large","cut flower","easy grow","popular"],                         score: 79, trend: "+2.0", trendDir: "up",     mentions: 13600, pos: 64, neu: 26, neg: 10, region: "Global",        season: "Summer/Autumn", breeder: "Unknown",    year: 1960, confidence: "medium" },
  { id: 109, name: "Cosmos 'Rubenza'",           aka: "Rubenza Cosmos",           zhName: "鲁本扎波斯菊", category: "Cosmos",        tags: ["ruby red","unique","cut flower","award","trending"],                         score: 81, trend: "+3.8", trendDir: "up",     mentions: 11800, pos: 67, neu: 24, neg: 9,  region: "Europe",        season: "Summer/Autumn", breeder: "Hem Genetics", year: 2012, confidence: "medium" },

  // ============================================================
  // PROTEA — 帝王花
  // ============================================================
  { id: 110, name: "Protea 'Pink Ice'",          aka: "Pink Ice Protea",          zhName: "粉冰帝王花",   category: "Protea",       tags: ["pink","dramatic","cut flower","dried","South African","long lasting"],      score: 84, trend: "+4.1", trendDir: "up",     mentions: 17600, pos: 70, neu: 22, neg: 8,  region: "Global",        season: "Autumn/Winter", breeder: "South Africa", year: 1970, confidence: "medium" },
  { id: 111, name: "Protea 'Repens'",            aka: "Sugarbush Protea",         zhName: "糖灌木帝王花", category: "Protea",        tags: ["white pink","honey","dried","South African","wildlife"],                    score: 79, trend: "+2.3", trendDir: "up",     mentions: 11200, pos: 64, neu: 26, neg: 10, region: "Global",        season: "Autumn/Winter", breeder: "Wild species", year: 1800, confidence: "low" },

  // ============================================================
  // ANTHURIUM — 红掌
  // ============================================================
  { id: 112, name: "Anthurium 'Midori'",         aka: "Midori Anthurium",         zhName: "绿色红掌",     category: "Anthurium",    tags: ["green","unique","indoor","long lasting","novelty","florist"],               score: 82, trend: "+3.4", trendDir: "up",     mentions: 14800, pos: 68, neu: 23, neg: 9,  region: "Asia",          season: "Year-round",    breeder: "Various",    year: 2000, confidence: "medium" },
  { id: 113, name: "Anthurium 'Alabama'",        aka: "Alabama Red Anthurium",    zhName: "阿拉巴马红掌", category: "Anthurium",    tags: ["red","classic","indoor","popular","long lasting","cut flower"],             score: 80, trend: "+1.8", trendDir: "up",     mentions: 18600, pos: 66, neu: 24, neg: 10, region: "Global",        season: "Year-round",    breeder: "Various",    year: 1990, confidence: "medium" },

  // ============================================================
  // STATICE / LIMONIUM — 勿忘我 / 补血草
  // ============================================================
  { id: 114, name: "Limonium 'QIS'",             aka: "QIS Statice",              zhName: "QIS补血草",    category: "Statice",      tags: ["cut flower","dried","purple","popular","florist","filler"],                 score: 76, trend: "+1.2", trendDir: "up",     mentions: 10800, pos: 61, neu: 28, neg: 11, region: "Global",        season: "Summer",        breeder: "Various",    year: 1985, confidence: "medium" },

  // ============================================================
  // GYPSOPHILA — 满天星
  // ============================================================
  { id: 115, name: "Gypsophila 'Million Stars'", aka: "Million Stars Baby's Breath", zhName: "百万星满天星", category: "Gypsophila",  tags: ["white","filler","cut flower","wedding","popular","florist"],               score: 85, trend: "+3.6", trendDir: "up",     mentions: 22400, pos: 71, neu: 21, neg: 8,  region: "Global",        season: "Year-round",    breeder: "Various",    year: 1990, confidence: "high" },

  // ============================================================
  // CALLA LILY — 马蹄莲
  // ============================================================
  { id: 116, name: "Zantedeschia 'Schwarzwalder'", aka: "Black Magic Calla",      zhName: "黑魔法马蹄莲", category: "Calla Lily",   tags: ["dark purple","dramatic","cut flower","wedding","unique","popular"],         score: 86, trend: "+4.2", trendDir: "up",     mentions: 19800, pos: 72, neu: 20, neg: 8,  region: "Global",        season: "Summer",        breeder: "Various",    year: 1990, confidence: "medium" },
  { id: 117, name: "Zantedeschia 'Crystal Blush'", aka: "Crystal Blush Calla",    zhName: "水晶红晕马蹄莲", category: "Calla Lily", tags: ["white pink","blush","wedding","elegant","cut flower"],                      score: 82, trend: "+2.8", trendDir: "up",     mentions: 14200, pos: 68, neu: 23, neg: 9,  region: "Global",        season: "Summer",        breeder: "Various",    year: 2000, confidence: "medium" },

  // ============================================================
  // STOCK — 紫罗兰
  // ============================================================
  { id: 118, name: "Matthiola 'Katz'",           aka: "Katz Stock",               zhName: "卡茨紫罗兰",   category: "Stock",        tags: ["fragrant","cut flower","florist","popular","spring"],                       score: 81, trend: "+2.1", trendDir: "up",     mentions: 12400, pos: 67, neu: 24, neg: 9,  region: "Europe",        season: "Spring",        breeder: "Katz Holland", year: 1990, confidence: "medium" },

  // ============================================================
  // ALSTROEMERIA — 六出花
  // ============================================================
  { id: 119, name: "Alstroemeria 'Inticancha'",  aka: "Inticancha Alstroemeria",  zhName: "印加花六出花",  category: "Alstroemeria", tags: ["compact","garden","long blooming","award","patio"],                         score: 83, trend: "+3.4", trendDir: "up",     mentions: 13800, pos: 69, neu: 22, neg: 9,  region: "Europe",        season: "Summer",        breeder: "Könst Alstroemeria", year: 2010, confidence: "medium" },
  { id: 120, name: "Alstroemeria 'Inca Ice'",    aka: "Inca Ice",                 zhName: "印加冰六出花",  category: "Alstroemeria", tags: ["peach","cut flower","long vase life","florist","popular"],                  score: 80, trend: "+2.0", trendDir: "up",     mentions: 11200, pos: 65, neu: 25, neg: 10, region: "Global",        season: "Summer",        breeder: "Various",    year: 2000, confidence: "medium" },

];

// ============================================================
// SEARCH ENGINE — Fuzzy + Multi-field Matching
// ============================================================

/**
 * Normalize a string for comparison:
 * lowercase, remove quotes/apostrophes/hyphens, collapse spaces
 */
function normalizeStr(s) {
  return (s || '').toLowerCase()
    .replace(/[''`\-]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Levenshtein distance for fuzzy matching
 */
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  const dp = Array.from({ length: m + 1 }, (_, i) => [i]);
  for (let j = 1; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i-1] === b[j-1]
        ? dp[i-1][j-1]
        : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
    }
  }
  return dp[m][n];
}

/**
 * Score a variety against a query.
 * Returns a relevance score (higher = more relevant), or -1 if no match.
 * 
 * Matching tiers (descending priority):
 *   10 — Exact match on name or zhName
 *    8 — Starts-with match on name, aka, or zhName
 *    6 — Substring match on name, aka, zhName, or category
 *    4 — Tag match
 *    2 — Fuzzy match (Levenshtein ≤ 2 on any token)
 *   -1 — No match
 */
function scoreVariety(variety, query) {
  if (!query) return 6; // Show all when no query

  const q = normalizeStr(query);
  const tokens = q.split(' ').filter(t => t.length >= 2);

  const fields = [
    normalizeStr(variety.name),
    normalizeStr(variety.aka || ''),
    normalizeStr(variety.zhName || ''),
    normalizeStr(variety.category),
    normalizeStr(variety.breeder || ''),
  ];

  const tagStr = normalizeStr((variety.tags || []).join(' '));

  // Tier 1: Exact match
  for (const f of fields) {
    if (f === q) return 10;
  }

  // Tier 2: Starts-with
  for (const f of fields) {
    if (f.startsWith(q)) return 8;
  }

  // Tier 3: Substring in primary fields
  for (const f of fields) {
    if (f.includes(q)) return 6;
  }

  // Tier 4: All query tokens found across fields
  const allFieldsStr = fields.join(' ') + ' ' + tagStr;
  if (tokens.length > 1 && tokens.every(t => allFieldsStr.includes(t))) return 5;

  // Tier 5: Tag match
  if (tagStr.includes(q)) return 4;
  if (tokens.some(t => tagStr.includes(t))) return 3;

  // Tier 6: Fuzzy match on individual tokens
  const allTokens = allFieldsStr.split(' ').filter(t => t.length >= 3);
  for (const qt of tokens) {
    if (qt.length < 3) continue;
    for (const ft of allTokens) {
      if (ft.length < 3) continue;
      const maxDist = qt.length <= 4 ? 1 : 2;
      if (levenshtein(qt, ft) <= maxDist) return 2;
    }
  }

  return -1; // No match
}

/**
 * Main search function.
 * Returns sorted array of { variety, relevance } objects.
 * 
 * @param {string} query - Search query
 * @param {Object} filters - { category, region, season }
 * @returns {Array} Filtered and sorted variety objects
 */
function searchVarieties(query, filters = {}) {
  let results = MASTER_VARIETY_INDEX.map(v => ({
    variety: v,
    relevance: scoreVariety(v, query)
  })).filter(r => r.relevance >= 0);

  // Apply dropdown filters
  if (filters.category && filters.category !== 'All Categories') {
    results = results.filter(r => r.variety.category === filters.category);
  }
  if (filters.region && filters.region !== 'Global' && filters.region !== '') {
    results = results.filter(r =>
      r.variety.region === filters.region || r.variety.region === 'Global'
    );
  }
  if (filters.season && filters.season !== 'All Seasons' && filters.season !== '') {
    results = results.filter(r =>
      r.variety.season && r.variety.season.toLowerCase().includes(filters.season.toLowerCase())
    );
  }

  // Sort: by relevance desc, then by score desc
  results.sort((a, b) => {
    if (b.relevance !== a.relevance) return b.relevance - a.relevance;
    return b.variety.score - a.variety.score;
  });

  return results.map(r => r.variety);
}

/**
 * Get autocomplete suggestions (top 8 matches)
 */
function getAutocompleteSuggestions(query) {
  if (!query || query.length < 1) return [];
  return searchVarieties(query).slice(0, 8);
}

/**
 * Get all unique categories from the index
 */
function getAllCategories() {
  return [...new Set(MASTER_VARIETY_INDEX.map(v => v.category))].sort();
}

/**
 * Get variety by ID
 */
function getVarietyById(id) {
  return MASTER_VARIETY_INDEX.find(v => v.id === id);
}

/**
 * Get top N varieties by score
 */
function getTopVarieties(n = 10) {
  return [...MASTER_VARIETY_INDEX]
    .sort((a, b) => b.score - a.score)
    .slice(0, n);
}

/**
 * Get rising varieties (highest positive trend)
 */
function getRisingVarieties(n = 10) {
  return [...MASTER_VARIETY_INDEX]
    .filter(v => v.trendDir === 'up')
    .sort((a, b) => parseFloat(b.trend) - parseFloat(a.trend))
    .slice(0, n);
}

/**
 * Get declining varieties
 */
function getDecliningVarieties(n = 10) {
  return [...MASTER_VARIETY_INDEX]
    .filter(v => v.trendDir === 'down')
    .sort((a, b) => parseFloat(a.trend) - parseFloat(b.trend))
    .slice(0, n);
}
