# MiniMax Voice Catalog

Complete reference for all available voices in the MiniMax Voice API.

## Contents

- [Voice Recommendation](#voice-recommendation) - Find voices by content type and characteristics
- [System Voices List (categorized by language)](#system-voices-list-categorized-by-language) - Complete voice database by language
- [Voice Parameters](#voice-parameters) - Configure voice settings (speed, volume, pitch, emotion)
- [Custom Voices](#custom-voices) - Voice cloning and voice design options
- [Voice Comparison Table](#voice-comparison-table) - Quick reference comparison
- [Voice IDs for Quick Reference](#voice-ids-for-quick-reference) - Most popular voices at a glance

---

## 1. How to Choose a Voice

When selecting a voice, follow this two-step decision process to ensure the voice matches the scenario, gender, age, and language of the character.

### Step 1: Identify the Usage Scenario

First, determine whether your content falls into one of the **three professional domains** listed in **Section 2.1**:

| Professional Domain | Examples |
|---|---|
| **Narration & Narrator in Storytelling** | suitable for the narrator in Audiobooks, fiction narration, storytelling |
| **News & Announcements** | suitable for news broadcasts, formal announcements, press releases |
| **Documentary** | suitable for documentary narration, commentary, educational films |

**If your content matches one of these professional domains:**
→ Prioritize selecting from the recommended voices in **Section 2.1**, filtering by scenario and the speaker's **gender**.
These voices are specifically optimized for their respective professional use cases (pacing, clarity, tone).

**If your content does NOT fall into these three professional domains:**
→ Proceed to Step 2 below.

### Step 2: Select by Character Traits (Gender + Age + Language)

For non-professional scenarios, select a voice from **Section 2.2** based on the following three character traits, in strict priority order:

1. **Gender** (highest priority, non-negotiable)
   - Male characters → **must** use male voices
   - Female characters → **must** use female voices
   - Never mismatch gender, even if other traits seem to fit

2. **Age** (determines which subsection to look in)
   - **Children** → Section 2.2 "Children's Voices"
   - **Youth** (teens, young adults) → Section 2.2 "Youthful Voices"
   - **Adult** → Section 2.2 "Adult Voices"
   - **Elderly** → Section 2.2 "Elderly Voices"

3. **Language** (must match the content language)
   - The voice **must** match the language of the content being generated
   - Chinese content → select Chinese voices; Korean content → select Korean voices; English content → select English voices, etc.
   - If no exact language match exists in Section 2.2, fall back to the full **System Voices List** (Section 3) for the target language

After narrowing down candidates by these three traits, choose the best match based on the voice's **personality**, **tone**, and **use case** as described in each voice entry.

### Quick Reference Decision Flow

```
Content Type?
├── Story/Narration/News/Documentary → Section 2.1 (filter by scenario + gender)
└── Other scenarios → Section 2.2:
    ├── 1. Match Gender (mandatory)
    ├── 2. Match Age Group (Children/Youth/Adult/Elderly/Professional)
    ├── 3. Match Language (must match content language)
    └── 4. Choose best fit by personality/tone
```

---


## 2. Voice Recommendation

### 2.1 By Content Type

**Narration & Narrator in Storytelling**
- Recommended: `audiobook_female_1`, `audiobook_male_1`
- Characteristics: suitable for narrating stories, sustained performance, clear articulation, good pacing

**News & Announcements**
- Recommended: `Chinese (Mandarin)_News_Anchor`, `Chinese (Mandarin)_Male_Announcer`
- Characteristics: Authoritative, clear, professional pacing

**Documentary**
- Recommended: `doc_commentary`
- Characteristics: Professional, clear, consistent pacing


### 2.2 By Characteristics

#### Children's Voices

| voice_id | Name | Description | Best For | Language |
|----------|------|-------------|----------|----------|
| `clever_boy` | 聪明男童 | Smart, witty boy voice | Children's content, educational | Chinese (Mandarin) |
| `cute_boy` | 可爱男童 | Adorable young boy voice | Kids' content, animations | Chinese (Mandarin) |
| `lovely_girl` | 萌萌女童 | Cute, sweet girl voice | Children's stories, games | Chinese (Mandarin) |
| `cartoon_pig` | 卡通猪小琪 | Cartoon character voice | Animations, comedy, entertainment | Chinese (Mandarin) |
| `Korean_SweetGirl` | Sweet Girl | Sweet, adorable young girl voice | Children's content, romance | Korean |
| `Indonesian_SweetGirl` | Sweet Girl | Sweet, adorable girl voice | Children's content, friendly | Indonesian |
| `English_Sweet_Girl` | Sweet Girl | Sweet, innocent young girl voice | Children's content, friendly | English |
| `Spanish_Kind-heartedGirl` | Kind-hearted Girl | Warm, compassionate girl voice | Children's content, warm | Spanish |
| `Portuguese_Kind-heartedGirl` | Kind-hearted Girl | Warm, compassionate girl voice | Children's content, warm | Portuguese |

#### Youthful Voices

| voice_id | Name | Description | Best For | Language |
|----------|------|-------------|----------|----------|
| `male-qn-qingse` | 青涩青年 | Youthful, inexperienced young man voice | Campus stories, coming-of-age content | Chinese (Mandarin) |
| `male-qn-daxuesheng` | 青年大学生 | Young university student voice | Campus content, educational | Chinese (Mandarin) |
| `female-shaonv` | 少女 | Young maiden voice | Romance, youth content | Chinese (Mandarin) |
| `bingjiao_didi` | 病娇弟弟 | Tsundere young brother voice | Romance, character-driven content | Chinese (Mandarin) |
| `junlang_nanyou` | 俊朗男友 | Handsome boyfriend voice | Romance, dating content | Chinese (Mandarin) |
| `chunzhen_xuedi` | 纯真学弟 | Innocent junior student voice | Campus stories, youth content | Chinese (Mandarin) |
| `lengdan_xiongzhang` | 冷淡学长 | Cool senior student voice | Campus stories, romance | Chinese (Mandarin) |
| `diadia_xuemei` | 嗲嗲学妹 | Flirty junior girl voice | Romance, dating content | Chinese (Mandarin) |
| `danya_xuejie` | 淡雅学姐 | Elegant senior girl voice | Campus stories, romance | Chinese (Mandarin) |
| `Chinese (Mandarin)_Straightforward_Boy` | 率真弟弟 | Frank, straightforward boy voice | Casual, direct content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Sincere_Adult` | 真诚青年 | Sincere young adult voice | Honest, genuine content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Pure-hearted_Boy` | 清澈邻家弟弟 | Pure-hearted neighbor boy voice | Innocent, wholesome content | Chinese (Mandarin) |
| `Korean_CheerfulBoyfriend` | Cheerful Boyfriend | Energetic, loving boyfriend voice | Romance, dating content | Korean |
| `Korean_ShyGirl` | Shy Girl | Timid, reserved girl voice | Comedy, romance | Korean |
| `Japanese_SportyStudent` | Sporty Student | Energetic athletic student voice | Sports, youth content | Japanese |
| `Japanese_InnocentBoy` | Innocent Boy | Pure, naive young boy voice | Children's content | Japanese |
| `Spanish_SincereTeen` | SincereTeen | Honest, genuine teenager voice | Youth, authentic | Spanish |
| `Spanish_Strong-WilledBoy` | Strong-willed Boy | Determined, persistent boy voice | Youth, motivation | Spanish |

#### Adult Voices

| voice_id | Name | Description | Best For | Language |
|----------|------|-------------|----------|----------|
| `female-chengshu` | 成熟女性 | Mature woman voice | Sophisticated, adult content | Chinese (Mandarin) |
| `female-yujie` | 御姐 | Mature, elegant woman voice | Romance, professional content | Chinese (Mandarin) |
| `female-tianmei` | 甜美女性 | Sweet, pleasant woman voice | Soft, gentle content | Chinese (Mandarin) |
| `badao_shaoye` | 霸道少爷 | Arrogant young master voice | Drama, character roles | Chinese (Mandarin) |
| `wumei_yujie` | 妩媚御姐 | Charming mature woman voice | Romance, mature content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Gentleman` | 温润男声 | Gentle, refined male voice | Narration, storytelling | Chinese (Mandarin) |
| `Chinese (Mandarin)_Unrestrained_Young_Man` | 不羁青年 | Unrestrained young man voice | Casual, entertainment content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Southern_Young_Man` | 南方小哥 | Southern young man voice | Regional character, casual content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Gentle_Youth` | 温润青年 | Gentle young man voice | Narration, calm content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Warm_Girl` | 温暖少女 | Warm young girl voice | Friendly, supportive content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 | Soft, gentle girl voice | Calm, soothing content | Chinese (Mandarin) |
| `Korean_PlayboyCharmer` | Playboy Charmer | Smooth, flirtatious male voice | Romance, entertainment | Korean |
| `Korean_CalmLady` | Calm Lady | Composed, serene female voice | Meditation, relaxation | Korean |
| `Spanish_ConfidentWoman` | Confident Woman | Self-assured, capable woman voice | Professional, empowerment | Spanish |
| `Portuguese_ConfidentWoman` | Confident Woman | Self-assured, capable woman voice | Professional, empowerment | Portuguese |

#### Elderly Voices

| voice_id | Name | Description | Best For | Language |
|----------|------|-------------|----------|----------|
| `Chinese (Mandarin)_Humorous_Elder` | 搞笑大爷 | Humorous old man voice | Comedy, entertainment | Chinese (Mandarin) |
| `Chinese (Mandarin)_Kind-hearted_Elder` | 花甲奶奶 | Kind elderly lady voice | Stories, warm content | Chinese (Mandarin) |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 热心大婶 | Kind-hearted auntie voice | Warm, friendly content | Chinese (Mandarin) |
| `Japanese_IntellectualSenior` | Intellectual Senior | Wise, knowledgeable elder voice | Narration, educational | Japanese |
| `Korean_IntellectualSenior` | Intellectual Senior | Wise, knowledgeable elder voice | Educational, narration | Korean |
| `Spanish_Wiselady` | Wise Lady | Experienced, wise woman voice | Guidance, advice | Spanish |
| `Portuguese_Wiselady` | Wise Lady | Experienced, wise woman voice | Guidance, advice | Portuguese |
| `Spanish_SereneElder` | Serene Elder | Calm, peaceful elderly voice | Meditation, wisdom | Spanish |
| `Portuguese_SereneElder` | Serene Elder | Calm, peaceful elderly voice | Meditation, wisdom | Portuguese |
| `English_Gentle-voiced_man` | Gentle-voiced Man | Soft-spoken, kind male voice | Calm, supportive content | English |

---

## System Voices List (categorized by language)

### Chinese Mandarin Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `male-qn-qingse` | 青涩青年 | Youthful, inexperienced young man voice | Campus stories, coming-of-age content |
| `male-qn-badao` | 霸道青年 | Arrogant, dominant young man voice | Drama, romance, character roles |
| `male-qn-daxuesheng` | 青年大学生 | Young university student voice | Campus content, educational |
| `female-shaonv` | 少女 | Young maiden voice | Romance, youth content |
| `female-yujie` | 御姐 | Mature, elegant woman voice | Romance, professional content |
| `female-chengshu` | 成熟女性 | Mature woman voice | Sophisticated, adult content |
| `female-tianmei` | 甜美女性 | Sweet, pleasant woman voice | Soft, gentle content |
| `clever_boy` | 聪明男童 | Smart, witty boy voice | Children's content, educational |
| `cute_boy` | 可爱男童 | Adorable young boy voice | Kids' content, animations |
| `lovely_girl` | 萌萌女童 | Cute, sweet girl voice | Children's stories, games |
| `cartoon_pig` | 卡通猪小琪 | Cartoon character voice | Animations, comedy, entertainment |
| `bingjiao_didi` | 病娇弟弟 | Tsundere young brother voice | Romance, character-driven content |
| `junlang_nanyou` | 俊朗男友 | Handsome boyfriend voice | Romance, dating content |
| `chunzhen_xuedi` | 纯真学弟 | Innocent junior student voice | Campus stories, youth content |
| `lengdan_xiongzhang` | 冷淡学长 | Cool senior student voice | Campus stories, romance |
| `badao_shaoye` | 霸道少爷 | Arrogant young master voice | Drama, character roles |
| `tianxin_xiaoling` | 甜心小玲 | Sweet Xiao Ling voice | Character roles, animations |
| `qiaopi_mengmei` | 俏皮萌妹 | Playful cute girl voice | Comedy, light-hearted content |
| `wumei_yujie` | 妩媚御姐 | Charming mature woman voice | Romance, mature content |
| `diadia_xuemei` | 嗲嗲学妹 | Flirty junior girl voice | Romance, dating content |
| `danya_xuejie` | 淡雅学姐 | Elegant senior girl voice | Campus stories, romance |
| `Arrogant_Miss` | 嚣张小姐 | Arrogant young lady voice | Drama, character roles |
| `Robot_Armor` | 机械战甲 | Robotic armor voice | Sci-fi, game characters |
| `Chinese (Mandarin)_Reliable_Executive` | 沉稳高管 | Reliable executive voice | Corporate, business content |
| `Chinese (Mandarin)_News_Anchor` | 新闻女声 | News anchor female voice | News broadcasts, current affairs |
| `Chinese (Mandarin)_Mature_Woman` | 傲娇御姐 | Tsundere mature woman voice | Romance, character-driven content |
| `Chinese (Mandarin)_Unrestrained_Young_Man` | 不羁青年 | Unrestrained young man voice | Casual, entertainment content |
| `male-qn-jingying` | 精英青年 | Elite, ambitious young man voice | Business, professional content |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 热心大婶 | Kind-hearted auntie voice | Warm, friendly content |
| `Chinese (Mandarin)_HK_Flight_Attendant` | 港普空姐 | HK accent flight attendant voice | Regional character, entertainment |
| `Chinese (Mandarin)_Humorous_Elder` | 搞笑大爷 | Humorous old man voice | Comedy, entertainment |
| `Chinese (Mandarin)_Gentleman` | 温润男声 | Gentle, refined male voice | Narration, storytelling |
| `Chinese (Mandarin)_Warm_Bestie` | 温暖闺蜜 | Warm bestie female voice | Friendly, supportive content |
| `Chinese (Mandarin)_Male_Announcer` | 播报男声 | Male announcer voice | Announcements, broadcasts |
| `Chinese (Mandarin)_Sweet_Lady` | 甜美女声 | Sweet lady voice | Soft, gentle content |
| `Chinese (Mandarin)_Southern_Young_Man` | 南方小哥 | Southern young man voice | Regional character, casual content |
| `Chinese (Mandarin)_Wise_Women` | 阅历姐姐 | Experienced wise woman voice | Advice, guidance content |
| `Chinese (Mandarin)_Gentle_Youth` | 温润青年 | Gentle young man voice | Narration, calm content |
| `Chinese (Mandarin)_Warm_Girl` | 温暖少女 | Warm young girl voice | Friendly, supportive content |
| `Chinese (Mandarin)_Kind-hearted_Elder` | 花甲奶奶 | Kind elderly lady voice | Stories, warm content |
| `Chinese (Mandarin)_Cute_Spirit` | 憨憨萌兽 | Cute cartoon spirit voice | Animations, children's content |
| `Chinese (Mandarin)_Radio_Host` | 电台男主播 | Radio host male voice | Podcasts, radio shows |
| `Chinese (Mandarin)_Lyrical_Voice` | 抒情男声 | Lyrical male singing voice | Music, singing content |
| `Chinese (Mandarin)_Straightforward_Boy` | 率真弟弟 | Frank, straightforward boy voice | Casual, direct content |
| `Chinese (Mandarin)_Sincere_Adult` | 真诚青年 | Sincere young adult voice | Honest, genuine content |
| `Chinese (Mandarin)_Gentle_Senior` | 温柔学姐 | Gentle senior girl voice | Campus stories, supportive content |
| `Chinese (Mandarin)_Stubborn_Friend` | 嘴硬竹马 | Stubborn childhood friend voice | Drama, character-driven content |
| `Chinese (Mandarin)_Crisp_Girl` | 清脆少女 | Crisp, clear young girl voice | Clear, bright content |
| `Chinese (Mandarin)_Pure-hearted_Boy` | 清澈邻家弟弟 | Pure-hearted neighbor boy voice | Innocent, wholesome content |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 | Soft, gentle girl voice | Calm, soothing content |

### Chinese Cantonese Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Cantonese_ProfessionalHost（F)` | 专业女主持 | Professional female host voice | Cantonese broadcasts, hosting |
| `Cantonese_GentleLady` | 温柔女声 | Gentle Cantonese female voice | Soft, warm Cantonese content |
| `Cantonese_ProfessionalHost（M)` | 专业男主持 | Professional male host voice | Cantonese broadcasts, hosting |
| `Cantonese_PlayfulMan` | 活泼男声 | Playful Cantonese male voice | Entertainment, casual content |
| `Cantonese_CuteGirl` | 可爱女孩 | Cute Cantonese girl voice | Children's content, animations |
| `Cantonese_KindWoman` | 善良女声 | Kind Cantonese female voice | Warm, friendly content |

### English Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Santa_Claus` | Santa Claus | Festive, jolly male voice | Holiday content, children's stories |
| `Grinch` | Grinch | Whiny, mischievous voice | Comedy, entertainment, holiday |
| `Rudolph` | Rudolph | Cute, nasal reindeer voice | Children's content, holiday |
| `Arnold` | Arnold | Deep, robotic terminator voice | Sci-fi, action, character roles |
| `Charming_Santa` | Charming Santa | Smooth, charismatic Santa voice | Holiday, entertainment |
| `Charming_Lady` | Charming Lady | Elegant, sophisticated female voice | Professional, romance |
| `Sweet_Girl` | Sweet Girl | Sweet, innocent young girl voice | Children's content, friendly |
| `Cute_Elf` | Cute Elf | Playful, tiny elf voice | Fantasy, children's content |
| `Attractive_Girl` | Attractive Girl | Attractive, engaging female voice | Entertainment, marketing |
| `Serene_Woman` | Serene Woman | Calm, peaceful female voice | Meditation, relaxation |
| `English_Trustworthy_Man` | Trustworthy Man | Reliable, sincere male voice | Business, narration |
| `English_Graceful_Lady` | Graceful Lady | Elegant, refined female voice | Formal, professional |
| `English_Aussie_Bloke` | Aussie Bloke | Casual, friendly Australian male voice | Casual, entertainment |
| `English_Whispering_girl` | Whispering Girl | Soft, whisper voice | Romance, intimate content |
| `English_Diligent_Man` | Diligent Man | Hardworking, earnest male voice | Motivational, educational |
| `English_Gentle-voiced_man` | Gentle-voiced Man | Soft-spoken, kind male voice | Calm, supportive content |

### Japanese Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Japanese_IntellectualSenior` | Intellectual Senior | Wise, knowledgeable elder voice | Narration, educational |
| `Japanese_DecisivePrincess` | Decisive Princess | Confident, royal princess voice | Animation, games, drama |
| `Japanese_LoyalKnight` | Loyal Knight | Brave, faithful knight voice | Fantasy, games, stories |
| `Japanese_DominantMan` | Dominant Man | Powerful, commanding male voice | Action, leadership |
| `Japanese_SeriousCommander` | Serious Commander | Stern, authoritative commander voice | Military, games |
| `Japanese_ColdQueen` | Cold Queen | Distant, majestic queen voice | Drama, fantasy |
| `Japanese_DependableWoman` | Dependable Woman | Reliable, supportive female voice | Supportive, guidance |
| `Japanese_GentleButler` | Gentle Butler | Polite, refined servant voice | Comedy, animation |
| `Japanese_KindLady` | Kind Lady | Warm, gentle noblewoman voice | Warm, comforting |
| `Japanese_CalmLady` | Calm Lady | Composed, serene female voice | Meditation, relaxation |
| `Japanese_OptimisticYouth` | Optimistic Youth | Cheerful, positive young person voice | Youth content, motivation |
| `Japanese_GenerousIzakayaOwner` | Generous Izakaya Owner | Friendly, welcoming tavern owner voice | Casual, comedy |
| `Japanese_SportyStudent` | Sporty Student | Energetic athletic student voice | Sports, youth content |
| `Japanese_InnocentBoy` | Innocent Boy | Pure, naive young boy voice | Children's content |
| `Japanese_GracefulMaiden` | Graceful Maiden | Elegant, gentle young woman voice | Romance, drama |

### Korean Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Korean_SweetGirl` | Sweet Girl | Sweet, adorable young girl voice | Children's content, romance |
| `Korean_CheerfulBoyfriend` | Cheerful Boyfriend | Energetic, loving boyfriend voice | Romance, dating content |
| `Korean_EnchantingSister` | Enchanting Sister | Charming, captivating sister voice | Family, drama |
| `Korean_ShyGirl` | Shy Girl | Timid, reserved girl voice | Comedy, romance |
| `Korean_ReliableSister` | Reliable Sister | Trustworthy, dependable sister voice | Supportive, guidance |
| `Korean_StrictBoss` | Strict Boss | Authoritative, demanding boss voice | Business, drama |
| `Korean_SassyGirl` | Sassy Girl | Bold, witty girl voice | Comedy, entertainment |
| `Korean_ChildhoodFriendGirl` | Childhood Friend Girl | Familiar, friendly childhood friend voice | Romance, nostalgia |
| `Korean_PlayboyCharmer` | Playboy Charmer | Smooth, flirtatious male voice | Romance, entertainment |
| `Korean_ElegantPrincess` | Elegant Princess | Graceful, royal princess voice | Animation, fantasy |
| `Korean_BraveFemaleWarrior` | Brave Female Warrior | Courageous female warrior voice | Action, fantasy |
| `Korean_BraveYouth` | Brave Youth | Heroic young person voice | Action, youth |
| `Korean_CalmLady` | Calm Lady | Composed, serene female voice | Meditation, relaxation |
| `Korean_EnthusiasticTeen` | EnthusiasticTeen | Excited, energetic teenager voice | Youth content |
| `Korean_SoothingLady` | Soothing Lady | Calming, comforting female voice | Relaxation, support |
| `Korean_IntellectualSenior` | Intellectual Senior | Wise, knowledgeable elder voice | Educational, narration |
| `Korean_LonelyWarrior` | Lonely Warrior | Solitary, melancholic warrior voice | Drama, fantasy |
| `Korean_MatureLady` | MatureLady | Sophisticated, adult female voice | Professional, drama |
| `Korean_InnocentBoy` | Innocent Boy | Pure, naive young boy voice | Children's content |
| `Korean_CharmingSister` | Charming Sister | Attractive, delightful sister voice | Family, romance |
| `Korean_AthleticStudent` | Athletic Student | Sporty, energetic student voice | Sports, youth |
| `Korean_BraveAdventurer` | Brave Adventurer | Courageous explorer voice | Adventure, fantasy |
| `Korean_CalmGentleman` | Calm Gentleman | Composed, refined gentleman voice | Formal, professional |
| `Korean_WiseElf` | Wise Elf | Ancient, mystical elf voice | Fantasy, narration |
| `Korean_CheerfulCoolJunior` | Cheerful Cool Junior | Popular, friendly junior voice | Youth, entertainment |
| `Korean_DecisiveQueen` | Decisive Queen | Authoritative, commanding queen voice | Drama, fantasy |
| `Korean_ColdYoungMan` | Cold Young Man | Distant, aloof young man voice | Drama, romance |
| `Korean_MysteriousGirl` | Mysterious Girl | Enigmatic, secretive girl voice | Mystery, drama |
| `Korean_QuirkyGirl` | Quirky Girl | Eccentric, unique girl voice | Comedy, entertainment |
| `Korean_ConsiderateSenior` | Considerate Senior | Thoughtful, caring elder voice | Warm, supportive |
| `Korean_CheerfulLittleSister` | Cheerful Little Sister | Playful, adorable younger sister voice | Family, comedy |
| `Korean_DominantMan` | Dominant Man | Powerful, commanding male voice | Leadership, action |
| `Korean_AirheadedGirl` | Airheaded Girl | Bubbly, spacey girl voice | Comedy, entertainment |
| `Korean_ReliableYouth` | Reliable Youth | Trustworthy, dependable young person voice | Supportive, youth |
| `Korean_FriendlyBigSister` | Friendly Big Sister | Warm, protective elder sister voice | Family, support |
| `Korean_GentleBoss` | Gentle Boss | Kind, understanding boss voice | Business, supportive |
| `Korean_ColdGirl` | Cold Girl | Aloof, distant girl voice | Drama, romance |
| `Korean_HaughtyLady` | Haughty Lady | Arrogant, proud woman voice | Drama, comedy |
| `Korean_CharmingElderSister` | Charming Elder Sister | Attractive, graceful elder sister voice | Romance, family |
| `Korean_IntellectualMan` | Intellectual Man | Smart, knowledgeable male voice | Educational, professional |
| `Korean_CaringWoman` | Caring Woman | Nurturing, supportive woman voice | Supportive, warm |
| `Korean_WiseTeacher` | Wise Teacher | Experienced, knowledgeable teacher voice | Educational |
| `Korean_ConfidentBoss` | Confident Boss | Self-assured, capable boss voice | Business, leadership |
| `Korean_AthleticGirl` | Athletic Girl | Sporty, energetic girl voice | Sports, fitness |
| `Korean_PossessiveMan` | PossessiveMan | Intense, protective male voice | Romance, drama |
| `Korean_GentleWoman` | Gentle Woman | Soft-spoken, kind woman voice | Calm, supportive |
| `Korean_CockyGuy` | Cocky Guy | Confident, slightly arrogant male voice | Comedy, entertainment |
| `Korean_ThoughtfulWoman` | ThoughtfulWoman | Reflective, caring woman voice | Drama, support |
| `Korean_OptimisticYouth` | Optimistic Youth | Positive, hopeful young person voice | Motivation, youth |

### Spanish Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Spanish_SereneWoman` | Serene Woman | Calm, peaceful female voice | Relaxation, meditation |
| `Spanish_MaturePartner` | Mature Partner | Sophisticated, adult partner voice | Romance, drama |
| `Spanish_CaptivatingStoryteller` | Captivating Storyteller | Engaging, magnetic narrator voice | Audiobooks, storytelling |
| `Spanish_Narrator` | Narrator | Professional narrative voice | Documentaries, narration |
| `Spanish_WiseScholar` | Wise Scholar | Knowledgeable, wise scholar voice | Educational, historical |
| `Spanish_Kind-heartedGirl` | Kind-hearted Girl | Warm, compassionate girl voice | Children's content, warm |
| `Spanish_DeterminedManager` | Determined Manager | Ambitious, driven manager voice | Business, motivation |
| `Spanish_BossyLeader` | Bossy Leader | Commanding, authoritative leader voice | Leadership, drama |
| `Spanish_ReservedYoungMan` | Reserved Young Man | Quiet, introverted young man voice | Drama, realistic characters |
| `Spanish_ConfidentWoman` | Confident Woman | Self-assured, capable woman voice | Professional, empowerment |
| `Spanish_ThoughtfulMan` | ThoughtfulMan | Reflective, intelligent man voice | Educational, drama |
| `Spanish_Strong-WilledBoy` | Strong-willed Boy | Determined, persistent boy voice | Youth, motivation |
| `Spanish_SophisticatedLady` | SophisticatedLady | Elegant, refined woman voice | Formal, romance |
| `Spanish_RationalMan` | Rational Man | Logical, analytical man voice | Educational, business |
| `Spanish_AnimeCharacter` | Anime Character | Exaggerated anime-style voice | Animation, entertainment |
| `Spanish_Deep-tonedMan` | Deep-toned Man | Deep, resonant male voice | Attractive, commanding |
| `Spanish_Fussyhostess` | Fussy Hostess | Particular, demanding hostess voice | Comedy, drama |
| `Spanish_SincereTeen` | SincereTeen | Honest, genuine teenager voice | Youth, authentic |
| `Spanish_FrankLady` | Frank Lady | Direct, honest woman voice | Comedy, drama |
| `Spanish_Comedian` | Comedian | Humorous, entertaining voice | Comedy, entertainment |
| `Spanish_Debator` | Debator | Argumentative, persuasive voice | Debate, discussion |
| `Spanish_ToughBoss` | Tough Boss | Harsh, demanding boss voice | Business, drama |
| `Spanish_Wiselady` | Wise Lady | Experienced, wise woman voice | Guidance, advice |
| `Spanish_Steadymentor` | Steady Mentor | Reliable, supportive mentor voice | Educational, guidance |
| `Spanish_Jovialman` | Jovial Man | Cheerful, friendly man voice | Entertainment, casual |
| `Spanish_SantaClaus` | Santa Claus | Festive Santa voice | Holiday, children |
| `Spanish_Rudolph` | Rudolph | Reindeer voice | Holiday, children |
| `Spanish_Intonategirl` | Intonate Girl | Musical, melodic girl voice | Music, singing |
| `Spanish_Arnold` | Arnold | Robotic, mechanical voice | Sci-fi, action |
| `Spanish_Ghost` | Ghost | Spooky, ethereal voice | Horror, mystery |
| `Spanish_HumorousElder` | Humorous Elder | Funny, elderly person voice | Comedy, entertainment |
| `Spanish_EnergeticBoy` | Energetic Boy | Active, lively boy voice | Youth, sports |
| `Spanish_WhimsicalGirl` | Whimsical Girl | Playful, imaginative girl voice | Children's, fantasy |
| `Spanish_StrictBoss` | Strict Boss | Strict, demanding boss voice | Business, education |
| `Spanish_ReliableMan` | Reliable Man | Trustworthy, dependable man voice | Professional, support |
| `Spanish_SereneElder` | Serene Elder | Calm, peaceful elderly voice | Meditation, wisdom |
| `Spanish_AngryMan` | Angry Man | Frustrated, irritated male voice | Drama, comedy |
| `Spanish_AssertiveQueen` | Assertive Queen | Confident, commanding queen voice | Drama, fantasy |
| `Spanish_CaringGirlfriend` | Caring Girlfriend | Nurturing, loving girlfriend voice | Romance, relationship |
| `Spanish_PowerfulSoldier` | Powerful Soldier | Strong, brave soldier voice | Action, military |
| `Spanish_PassionateWarrior` | Passionate Warrior | Fierce, dedicated warrior voice | Action, fantasy |
| `Spanish_ChattyGirl` | Chatty Girl | Talkative, sociable girl voice | Comedy, social |
| `Spanish_RomanticHusband` | Romantic Husband | Loving, romantic husband voice | Romance, family |
| `Spanish_CompellingGirl` | CompellingGirl | Persuasive, magnetic girl voice | Marketing, entertainment |
| `Spanish_PowerfulVeteran` | Powerful Veteran | Experienced, strong veteran voice | Military, drama |
| `Spanish_SensibleManager` | Sensible Manager | Practical, reasonable manager voice | Business, guidance |
| `Spanish_ThoughtfulLady` | Thoughtful Lady | Considerate, kind lady voice | Supportive, advice |

### Portuguese Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Portuguese_SentimentalLady` | Sentimental Lady | Emotional, sensitive lady voice | Drama, romance |
| `Portuguese_BossyLeader` | Bossy Leader | Commanding, authoritative leader voice | Leadership, drama |
| `Portuguese_Wiselady` | Wise Lady | Experienced, wise woman voice | Guidance, advice |
| `Portuguese_Strong-WilledBoy` | Strong-willed Boy | Determined, persistent boy voice | Youth, motivation |
| `Portuguese_Deep-VoicedGentleman` | Deep-voiced Gentleman | Deep, rich male voice | Attractive, commanding |
| `Portuguese_UpsetGirl` | Upset Girl | Distressed, emotional girl voice | Drama, realistic |
| `Portuguese_PassionateWarrior` | Passionate Warrior | Fierce, dedicated warrior voice | Action, fantasy |
| `Portuguese_AnimeCharacter` | Anime Character | Exaggerated anime-style voice | Animation, entertainment |
| `Portuguese_ConfidentWoman` | Confident Woman | Self-assured, capable woman voice | Professional, empowerment |
| `Portuguese_AngryMan` | Angry Man | Frustrated, irritated male voice | Drama, comedy |
| `Portuguese_CaptivatingStoryteller` | Captivating Storyteller | Engaging, magnetic narrator voice | Audiobooks, storytelling |
| `Portuguese_Godfather` | Godfather | Authoritative, powerful father figure voice | Drama, powerful |
| `Portuguese_ReservedYoungMan` | Reserved Young Man | Quiet, introverted young man voice | Drama, realistic |
| `Portuguese_SmartYoungGirl` | Smart Young Girl | Intelligent, clever girl voice | Educational, youth |
| `Portuguese_Kind-heartedGirl` | Kind-hearted Girl | Warm, compassionate girl voice | Children's content, warm |
| `Portuguese_Pompouslady` | Pompous Lady | Self-important, arrogant lady voice | Comedy, drama |
| `Portuguese_Grinch` | Grinch | Whiny, mischievous voice | Comedy, entertainment |
| `Portuguese_Debator` | Debator | Argumentative, persuasive voice | Debate, discussion |
| `Portuguese_SweetGirl` | Sweet Girl | Sweet, adorable girl voice | Children's content, romance |
| `Portuguese_AttractiveGirl` | Attractive Girl | Charming, appealing girl voice | Entertainment, romance |
| `Portuguese_ThoughtfulMan` | Thoughtful Man | Reflective, intelligent man voice | Educational, drama |
| `Portuguese_PlayfulGirl` | Playful Girl | Playful, fun-loving girl voice | Comedy, children's content |
| `Portuguese_GorgeousLady` | Gorgeous Lady | Beautiful, stunning lady voice | Romance, entertainment |
| `Portuguese_LovelyLady` | Lovely Lady | Sweet, endearing lady voice | Warm, friendly |
| `Portuguese_SereneWoman` | Serene Woman | Calm, peaceful female voice | Relaxation, meditation |
| `Portuguese_SadTeen` | Sad Teen | Melancholic, teenage voice | Drama, emotional |
| `Portuguese_MaturePartner` | Mature Partner | Sophisticated, adult partner voice | Romance, drama |
| `Portuguese_Comedian` | Comedian | Humorous, entertaining voice | Comedy, entertainment |
| `Portuguese_NaughtySchoolgirl` | Naughty Schoolgirl | Mischievous, playful student voice | Comedy, school |
| `Portuguese_Narrator` | Narrator | Professional narrative voice | Documentaries, narration |
| `Portuguese_ToughBoss` | Tough Boss | Harsh, demanding boss voice | Business, drama |
| `Portuguese_Fussyhostess` | Fussy Hostess | Particular, demanding hostess voice | Comedy, drama |
| `Portuguese_Dramatist` | Dramatist | Theatrical, expressive voice | Drama, storytelling |
| `Portuguese_Steadymentor` | Steady Mentor | Reliable, supportive mentor voice | Educational, guidance |
| `Portuguese_Jovialman` | Jovial Man | Cheerful, friendly man voice | Entertainment, casual |
| `Portuguese_CharmingQueen` | Charming Queen | Elegant, captivating queen voice | Drama, fantasy |
| `Portuguese_SantaClaus` | Santa Claus | Festive Santa voice | Holiday, children |
| `Portuguese_Rudolph` | Rudolph | Reindeer voice | Holiday, children |
| `Portuguese_Arnold` | Arnold | Robotic, mechanical voice | Sci-fi, action |
| `Portuguese_CharmingSanta` | Charming Santa | Smooth, charismatic Santa voice | Holiday, entertainment |
| `Portuguese_CharmingLady` | Charming Lady | Elegant, sophisticated lady voice | Professional, romance |
| `Portuguese_Ghost` | Ghost | Spooky, ethereal voice | Horror, mystery |
| `Portuguese_HumorousElder` | Humorous Elder | Funny, elderly person voice | Comedy, entertainment |
| `Portuguese_CalmLeader` | Calm Leader | Composed, steady leader voice | Leadership, guidance |
| `Portuguese_GentleTeacher` | Gentle Teacher | Kind, patient teacher voice | Educational, supportive |
| `Portuguese_EnergeticBoy` | Energetic Boy | Active, lively boy voice | Youth, sports |
| `Portuguese_ReliableMan` | Reliable Man | Trustworthy, dependable man voice | Professional, support |
| `Portuguese_SereneElder` | Serene Elder | Calm, peaceful elderly voice | Meditation, wisdom |
| `Portuguese_GrimReaper` | Grim Reaper | Dark, ominous voice | Horror, fantasy |
| `Portuguese_AssertiveQueen` | Assertive Queen | Confident, commanding queen voice | Drama, fantasy |
| `Portuguese_WhimsicalGirl` | Whimsical Girl | Playful, imaginative girl voice | Children's, fantasy |
| `Portuguese_StressedLady` | Stressed Lady | Anxious, overwhelmed lady voice | Comedy, realistic |
| `Portuguese_FriendlyNeighbor` | Friendly Neighbor | Warm, helpful neighbor voice | Community, family |
| `Portuguese_CaringGirlfriend` | Caring Girlfriend | Nurturing, loving girlfriend voice | Romance, relationship |
| `Portuguese_PowerfulSoldier` | Powerful Soldier | Strong, brave soldier voice | Action, military |
| `Portuguese_FascinatingBoy` | Fascinating Boy | Charming, intriguing boy voice | Romance, youth |
| `Portuguese_RomanticHusband` | Romantic Husband | Loving, romantic husband voice | Romance, family |
| `Portuguese_StrictBoss` | Strict Boss | Strict, demanding boss voice | Business, education |
| `Portuguese_InspiringLady` | Inspiring Lady | Motivating, encouraging lady voice | Motivation, leadership |
| `Portuguese_PlayfulSpirit` | Playful Spirit | Cheerful, mischievous spirit voice | Fantasy, children's |
| `Portuguese_ElegantGirl` | Elegant Girl | Graceful, refined girl voice | Formal, romance |
| `Portuguese_CompellingGirl` | Compelling Girl | Persuasive, magnetic girl voice | Marketing, entertainment |
| `Portuguese_PowerfulVeteran` | Powerful Veteran | Experienced, strong veteran voice | Military, drama |
| `Portuguese_SensibleManager` | Sensible Manager | Practical, reasonable manager voice | Business, guidance |
| `Portuguese_ThoughtfulLady` | Thoughtful Lady | Considerate, kind lady voice | Supportive, advice |
| `Portuguese_TheatricalActor` | Theatrical Actor | Dramatic, expressive actor voice | Drama, entertainment |
| `Portuguese_FragileBoy` | Fragile Boy | Sensitive, vulnerable boy voice | Drama, emotional |
| `Portuguese_ChattyGirl` | Chatty Girl | Talkative, sociable girl voice | Comedy, social |
| `Portuguese_Conscientiousinstructor` | Conscientious Instructor | Careful, diligent instructor voice | Educational, training |
| `Portuguese_RationalMan` | Rational Man | Logical, analytical man voice | Educational, business |
| `Portuguese_WiseScholar` | Wise Scholar | Knowledgeable, wise scholar voice | Educational, historical |
| `Portuguese_FrankLady` | Frank Lady | Direct, honest woman voice | Comedy, drama |
| `Portuguese_DeterminedManager` | Determined Manager | Ambitious, driven manager voice | Business, motivation |

### French Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `French_Male_Speech_New` | Level-Headed Man | Calm, reasonable male voice | Professional, narration |
| `French_Female_News Anchor` | Patient Female Presenter | Clear, patient news presenter voice | News, broadcasts |
| `French_CasualMan` | Casual Man | Relaxed, informal male voice | Casual, entertainment |
| `French_MovieLeadFemale` | Movie Lead Female | Dramatic, expressive female voice | Drama, entertainment |
| `French_FemaleAnchor` | Female Anchor | Professional female anchor voice | News, broadcasts |

### Indonesian Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Indonesian_SweetGirl` | Sweet Girl | Sweet, adorable girl voice | Children's content, friendly |
| `Indonesian_ReservedYoungMan` | Reserved Young Man | Quiet, introverted young man voice | Drama, realistic |
| `Indonesian_CharmingGirl` | Charming Girl | Attractive, appealing girl voice | Entertainment, romance |
| `Indonesian_CalmWoman` | Calm Woman | Composed, peaceful female voice | Relaxation, meditation |
| `Indonesian_ConfidentWoman` | Confident Woman | Self-assured, capable woman voice | Professional, empowerment |
| `Indonesian_CaringMan` | Caring Man | Nurturing, supportive man voice | Supportive, family |
| `Indonesian_BossyLeader` | Bossy Leader | Commanding, authoritative leader voice | Leadership, drama |
| `Indonesian_DeterminedBoy` | Determined Boy | Ambitious, persistent boy voice | Youth, motivation |
| `Indonesian_GentleGirl` | Gentle Girl | Soft-spoken, kind girl voice | Calm, supportive |

### German Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `German_FriendlyMan` | Friendly Man | Warm, approachable male voice | Casual, friendly |
| `German_SweetLady` | Sweet Lady | Pleasant, kind lady voice | Warm, supportive |
| `German_PlayfulMan` | Playful Man | Fun-loving, humorous male voice | Comedy, entertainment |

### Russian Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Russian_HandsomeChildhoodFriend` | Handsome Childhood Friend | Charming childhood friend voice | Romance, nostalgia |
| `Russian_BrightHeroine` | Bright Queen | Lively, strong female lead voice | Drama, action |
| `Russian_AmbitiousWoman` | Ambitious Woman | Driven, determined woman voice | Professional, motivation |
| `Russian_ReliableMan` | Reliable Man | Trustworthy, dependable man voice | Professional, support |
| `Russian_CrazyQueen` | Crazy Girl | Wild, unpredictable female voice | Comedy, drama |
| `Russian_PessimisticGirl` | Pessimistic Girl | Gloomy, negative girl voice | Comedy, drama |
| `Russian_AttractiveGuy` | Attractive Guy | Charming, appealing male voice | Romance, entertainment |
| `Russian_Bad-temperedBoy` | Bad-tempered Boy | Irritable, grumpy boy voice | Comedy, drama |

### Italian Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Italian_BraveHeroine` | Brave Heroine | Courageous, heroic female voice | Action, fantasy |
| `Italian_Narrator` | Narrator | Professional narrative voice | Documentaries, storytelling |
| `Italian_WanderingSorcerer` | Wandering Sorcerer | Mysterious, traveling magician voice | Fantasy, adventure |
| `Italian_DiligentLeader` | Diligent Leader | Hardworking, dedicated leader voice | Leadership, business |

### Arabic Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Arabic_CalmWoman` | Calm Woman | Composed, peaceful female voice | Relaxation, meditation |
| `Arabic_FriendlyGuy` | Friendly Guy | Warm, approachable male voice | Casual, friendly |

### Turkish Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Turkish_CalmWoman` | Calm Woman | Composed, peaceful female voice | Relaxation, meditation |
| `Turkish_Trustworthyman` | Trustworthy Man | Reliable, sincere male voice | Professional, business |

### Ukrainian Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Ukrainian_CalmWoman` | Calm Woman | Composed, peaceful female voice | Relaxation, meditation |
| `Ukrainian_WiseScholar` | Wise Scholar | Knowledgeable, wise scholar voice | Educational, historical |

### Dutch Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Dutch_kindhearted_girl` | Kind-hearted girl | Warm, compassionate girl voice | Children's content, warm |
| `Dutch_bossy_leader` | Bossy leader | Commanding, authoritative leader voice | Leadership, drama |

### Vietnamese Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Vietnamese_kindhearted_girl` | Kind-hearted girl | Warm, compassionate girl voice | Children's content, warm |

### Thai Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Thai_male_1_sample8` | Serene Man | Calm, peaceful male voice | Relaxation, meditation |
| `Thai_male_2_sample2` | Friendly Man | Warm, approachable male voice | Casual, friendly |
| `Thai_female_1_sample1` | Confident Woman | Self-assured, capable woman voice | Professional, empowerment |
| `Thai_female_2_sample2` | Energetic Woman | Active, lively female voice | Motivation, energy |

### Polish Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Polish_male_1_sample4` | Male Narrator | Professional narrative voice | Documentaries, narration |
| `Polish_male_2_sample3` | Male Anchor | Professional male anchor voice | News, broadcasts |
| `Polish_female_1_sample1` | Calm Woman | Composed, peaceful female voice | Relaxation, meditation |
| `Polish_female_2_sample3` | Casual Woman | Relaxed, informal female voice | Casual, entertainment |

### Romanian Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `Romanian_male_1_sample2` | Reliable Man | Trustworthy, dependable man voice | Professional, support |
| `Romanian_male_2_sample1` | Energetic Youth | Active, lively young person voice | Youth, motivation |
| `Romanian_female_1_sample4` | Optimistic Youth | Positive, hopeful young person voice | Motivation, youth |
| `Romanian_female_2_sample1` | Gentle Woman | Soft-spoken, kind woman voice | Calm, supportive |

### Greek Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `greek_male_1a_v1` | Thoughtful Mentor | Reflective, wise mentor voice | Educational, guidance |
| `Greek_female_1_sample1` | Gentle Lady | Soft-spoken, kind lady voice | Calm, supportive |
| `Greek_female_2_sample3` | Girl Next Door | Friendly, approachable girl voice | Casual, friendly |

### Czech Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `czech_male_1_v1` | Assured Presenter | Confident, professional presenter voice | Presentations, broadcasts |
| `czech_female_5_v7` | Steadfast Narrator | Reliable, consistent narrator voice | Documentaries, storytelling |
| `czech_female_2_v2` | Elegant Lady | Graceful, refined lady voice | Formal, professional |

### Finnish Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `finnish_male_3_v1` | Upbeat Man | Cheerful, energetic male voice | Motivation, entertainment |
| `finnish_male_1_v2` | Friendly Boy | Warm, approachable boy voice | Children's content, friendly |
| `finnish_female_4_v1` | Assertive Woman | Confident, strong female voice | Professional, empowerment |

### Hindi Voices

| voice_id | Name | Description | Best For |
|----------|------|-------------|----------|
| `hindi_male_1_v2` | Trustworthy Advisor | Reliable, wise advisor voice | Guidance, advice |
| `hindi_female_2_v1` | Tranquil Woman | Calm, peaceful female voice | Relaxation, meditation |
| `hindi_female_1_v2` | News Anchor | Professional news anchor voice | News, broadcasts |

---

## Voice Parameters

### VoiceSetting Dataclass

```python
from utils import VoiceSetting

voice = VoiceSetting(
    voice_id="male-qn-qingse",  # Required: Voice ID
    speed=1.0,                   # Optional: 0.5 (slower) to 2.0 (faster), default 1.0
    volume=1.0,                  # Optional: 0.1 (quieter) to 10.0 (louder), default 1.0
    pitch=0,                     # Optional: -12 (deeper) to 12 (higher), default 0
    emotion="calm",           # Optional: happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper
)
```

### Parameter Guidelines

**Speed**
- 0.75: Slower, deliberate speech (news, tutorials)
- 1.0: Normal pace (most content)
- 1.25: Slightly faster (energetic content)
- 1.5+: Fast pace (time-sensitive content)

**Volume**
- 0.8-1.0: Normal listening levels
- 1.0-1.5: Louder for attention-grabbing content
- < 0.8: Softer, intimate feeling

**Pitch**
- -6 to -3: Deeper, more authoritative
- 0: Natural pitch
- +3 to +6: Higher, more energetic

**Emotion**
- `calm`: Calm, neutral tone
- `fluent`: Fluent, natural tone
- `whisper`: Whisper, soft, gentle tone
- `happy`: Cheerful, upbeat tone
- `sad`: Melancholic, somber tone
- `angry`: Frustrated, intense tone
- `fearful`: Anxious, nervous tone
- `disgusted`: Repulsed, revolted tone
- `surprised`: Astonished, amazed tone


## Custom Voices

### Voice Cloning

Create custom voices from audio samples for unique brand voices.

**Requirements:**
- Source audio: 10 seconds to 5 minutes
- Format: mp3, wav, m4a
- Size: Max 20MB
- Quality: Clear, no background noise, single speaker

**Best Practices:**
- Use 30-60 seconds of clean speech
- Include varied intonation and emotion
- Record in quiet environment
- Consistent volume throughout

### Voice Design

Generate new voices through text descriptions for creative projects.

**When to Use:**
- No existing voice matches your needs
- Need unique character voices
- Prototype before full voice cloning

**Prompt Guidelines:**
- Include: gender, age, vocal characteristics, emotional tone, use case
- Be specific about pacing, tone, and intended audience
- Example: "A warm, grandmotherly voice with gentle pacing, perfect for bedtime stories"

