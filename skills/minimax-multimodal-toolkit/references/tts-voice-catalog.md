# TTS Voice Catalog

## Contents

- [Voice Selection Guide](#voice-selection-guide)
- [System Voices by Language](#system-voices-by-language)
- [Voice Parameters](#voice-parameters)
- [Custom Voices](#custom-voices)

---

## Voice Selection Guide

### Decision Flow

```
Content type?
├── Narration / Audiobook  → audiobook_female_1, audiobook_male_1
├── News / Announcement    → Chinese (Mandarin)_News_Anchor, Chinese (Mandarin)_Male_Announcer
├── Documentary            → doc_commentary
└── Other                  → Select by: Gender → Age → Language → Personality
```

### Recommended Professional Voices

| Scenario | Recommended | Characteristics |
|----------|-------------|-----------------|
| Narration / Audiobook | `audiobook_female_1`, `audiobook_male_1` | Clear articulation, good pacing, sustained performance |
| News / Announcement | `Chinese (Mandarin)_News_Anchor`, `Chinese (Mandarin)_Male_Announcer` | Authoritative, professional pacing |
| Documentary | `doc_commentary` | Professional, clear, consistent |

### Selection Priority

1. **Gender** (mandatory match) — male voices for male characters, female for female
2. **Age** — Children / Youth / Adult / Elderly
3. **Language** (must match content language)
4. **Personality/tone** — choose best fit from matching candidates

---

## System Voices by Language

Gender: M = Male, F = Female, N = Neutral/Character
Age: C = Child, Y = Youth, A = Adult, E = Elder

### Chinese Mandarin (普通话)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `male-qn-qingse` | 青涩青年 | M | Y | Youthful, inexperienced | Campus, coming-of-age |
| `male-qn-badao` | 霸道青年 | M | Y | Arrogant, dominant | Drama, romance |
| `male-qn-daxuesheng` | 青年大学生 | M | Y | University student | Campus, educational |
| `male-qn-jingying` | 精英青年 | M | A | Elite, ambitious | Business, professional |
| `female-shaonv` | 少女 | F | Y | Young maiden | Romance, youth |
| `female-yujie` | 御姐 | F | A | Mature, elegant | Romance, professional |
| `female-chengshu` | 成熟女性 | F | A | Mature, reliable | Sophisticated, news |
| `female-tianmei` | 甜美女性 | F | A | Sweet, pleasant | Soft, gentle |
| `clever_boy` | 聪明男童 | M | C | Smart, witty | Children's, educational |
| `cute_boy` | 可爱男童 | M | C | Adorable | Kids, animations |
| `lovely_girl` | 萌萌女童 | F | C | Cute, sweet | Children's stories |
| `cartoon_pig` | 卡通猪小琪 | N | C | Cartoon character | Animations, comedy |
| `bingjiao_didi` | 病娇弟弟 | M | Y | Tsundere brother | Romance, character |
| `junlang_nanyou` | 俊朗男友 | M | Y | Handsome boyfriend | Romance, dating |
| `chunzhen_xuedi` | 纯真学弟 | M | Y | Innocent junior | Campus, youth |
| `lengdan_xiongzhang` | 冷淡学长 | M | Y | Cool senior | Campus, romance |
| `badao_shaoye` | 霸道少爷 | M | A | Arrogant young master | Drama, character |
| `tianxin_xiaoling` | 甜心小玲 | F | Y | Sweet Xiao Ling | Character, animations |
| `qiaopi_mengmei` | 俏皮萌妹 | F | Y | Playful cute girl | Comedy, light-hearted |
| `wumei_yujie` | 妩媚御姐 | F | A | Charming mature woman | Romance, mature |
| `diadia_xuemei` | 嗲嗲学妹 | F | Y | Flirty junior girl | Romance, dating |
| `danya_xuejie` | 淡雅学姐 | F | Y | Elegant senior girl | Campus, romance |
| `Arrogant_Miss` | 嚣张小姐 | F | A | Arrogant young lady | Drama, character |
| `Robot_Armor` | 机械战甲 | N | A | Robotic armor | Sci-fi, games |
| `audiobook_male_1` | 有声书男1 | M | A | Warm, engaging narrator | Audiobooks, stories |
| `audiobook_female_1` | 有声书女1 | F | A | Gentle, expressive narrator | Audiobooks, stories |
| `doc_commentary` | 纪录片解说 | M | A | Professional narrator | Documentary |
| `Chinese (Mandarin)_News_Anchor` | 新闻女声 | F | A | News anchor | News, broadcasts |
| `Chinese (Mandarin)_Male_Announcer` | 播报男声 | M | A | Male announcer | Announcements |
| `Chinese (Mandarin)_Radio_Host` | 电台男主播 | M | A | Radio host | Podcasts, radio |
| `Chinese (Mandarin)_Reliable_Executive` | 沉稳高管 | M | A | Reliable executive | Corporate, business |
| `Chinese (Mandarin)_Gentleman` | 温润男声 | M | A | Gentle, refined | Narration, storytelling |
| `Chinese (Mandarin)_Unrestrained_Young_Man` | 不羁青年 | M | Y | Unrestrained, casual | Entertainment |
| `Chinese (Mandarin)_Southern_Young_Man` | 南方小哥 | M | Y | Southern accent | Regional, casual |
| `Chinese (Mandarin)_Gentle_Youth` | 温润青年 | M | Y | Gentle young man | Narration, calm |
| `Chinese (Mandarin)_Sincere_Adult` | 真诚青年 | M | Y | Sincere, genuine | Honest, genuine |
| `Chinese (Mandarin)_Straightforward_Boy` | 率真弟弟 | M | Y | Frank, direct | Casual, direct |
| `Chinese (Mandarin)_Pure-hearted_Boy` | 清澈邻家弟弟 | M | Y | Pure-hearted neighbor | Innocent, wholesome |
| `Chinese (Mandarin)_Stubborn_Friend` | 嘴硬竹马 | M | Y | Stubborn childhood friend | Drama, character |
| `Chinese (Mandarin)_Lyrical_Voice` | 抒情男声 | M | A | Lyrical, singing | Music, singing |
| `Chinese (Mandarin)_Mature_Woman` | 傲娇御姐 | F | A | Tsundere mature woman | Romance, character |
| `Chinese (Mandarin)_Sweet_Lady` | 甜美女声 | F | A | Sweet lady | Soft, gentle |
| `Chinese (Mandarin)_Warm_Bestie` | 温暖闺蜜 | F | A | Warm bestie | Friendly, supportive |
| `Chinese (Mandarin)_Warm_Girl` | 温暖少女 | F | Y | Warm young girl | Friendly, supportive |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 | F | Y | Soft, gentle | Calm, soothing |
| `Chinese (Mandarin)_Crisp_Girl` | 清脆少女 | F | Y | Crisp, clear | Bright, clear |
| `Chinese (Mandarin)_Gentle_Senior` | 温柔学姐 | F | Y | Gentle senior girl | Campus, supportive |
| `Chinese (Mandarin)_Wise_Women` | 阅历姐姐 | F | A | Experienced, wise | Advice, guidance |
| `Chinese (Mandarin)_HK_Flight_Attendant` | 港普空姐 | F | A | HK accent flight attendant | Regional, entertainment |
| `Chinese (Mandarin)_Cute_Spirit` | 憨憨萌兽 | N | C | Cute cartoon spirit | Animations, children's |
| `Chinese (Mandarin)_Humorous_Elder` | 搞笑大爷 | M | E | Humorous old man | Comedy, entertainment |
| `Chinese (Mandarin)_Kind-hearted_Elder` | 花甲奶奶 | F | E | Kind elderly lady | Stories, warm |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 热心大婶 | F | E | Kind-hearted auntie | Warm, friendly |

### Chinese Cantonese (粤语)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Cantonese_ProfessionalHost（F)` | 专业女主持 | F | A | Professional host | Broadcasts, hosting |
| `Cantonese_GentleLady` | 温柔女声 | F | A | Gentle female | Soft, warm |
| `Cantonese_ProfessionalHost（M)` | 专业男主持 | M | A | Professional host | Broadcasts, hosting |
| `Cantonese_PlayfulMan` | 活泼男声 | M | A | Playful male | Entertainment, casual |
| `Cantonese_CuteGirl` | 可爱女孩 | F | C | Cute girl | Children's, animations |
| `Cantonese_KindWoman` | 善良女声 | F | A | Kind female | Warm, friendly |

### English

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `English_Trustworthy_Man` | Trustworthy Man | M | A | Reliable, sincere | Business, narration |
| `English_Graceful_Lady` | Graceful Lady | F | A | Elegant, refined | Formal, professional |
| `English_Aussie_Bloke` | Aussie Bloke | M | A | Casual Australian | Casual, entertainment |
| `English_Whispering_girl` | Whispering Girl | F | Y | Soft whisper | Romance, intimate |
| `English_Diligent_Man` | Diligent Man | M | A | Earnest, hardworking | Motivational, educational |
| `English_Gentle-voiced_man` | Gentle-voiced Man | M | E | Soft-spoken, kind | Calm, supportive |
| `English_Sweet_Girl` | Sweet Girl | F | C | Sweet, innocent | Children's, friendly |
| `Charming_Lady` | Charming Lady | F | A | Elegant, sophisticated | Professional, romance |
| `Attractive_Girl` | Attractive Girl | F | Y | Engaging female | Entertainment, marketing |
| `Serene_Woman` | Serene Woman | F | A | Calm, peaceful | Meditation, relaxation |
| `Santa_Claus` | Santa Claus | M | E | Festive, jolly | Holiday, children's |
| `Charming_Santa` | Charming Santa | M | E | Smooth, charismatic | Holiday, entertainment |
| `Grinch` | Grinch | M | A | Whiny, mischievous | Comedy, holiday |
| `Rudolph` | Rudolph | N | C | Cute, nasal reindeer | Children's, holiday |
| `Arnold` | Arnold | M | A | Deep, robotic | Sci-fi, action |
| `Cute_Elf` | Cute Elf | N | C | Playful, tiny elf | Fantasy, children's |

### Japanese (日本語)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Japanese_IntellectualSenior` | Intellectual Senior | M | E | Wise, knowledgeable | Narration, educational |
| `Japanese_DecisivePrincess` | Decisive Princess | F | A | Confident, royal | Animation, games |
| `Japanese_LoyalKnight` | Loyal Knight | M | A | Brave, faithful | Fantasy, games |
| `Japanese_DominantMan` | Dominant Man | M | A | Powerful, commanding | Action, leadership |
| `Japanese_SeriousCommander` | Serious Commander | M | A | Stern, authoritative | Military, games |
| `Japanese_ColdQueen` | Cold Queen | F | A | Distant, majestic | Drama, fantasy |
| `Japanese_DependableWoman` | Dependable Woman | F | A | Reliable, supportive | Guidance |
| `Japanese_GentleButler` | Gentle Butler | M | A | Polite, refined | Comedy, animation |
| `Japanese_KindLady` | Kind Lady | F | A | Warm, gentle | Comforting |
| `Japanese_CalmLady` | Calm Lady | F | A | Composed, serene | Meditation, relaxation |
| `Japanese_OptimisticYouth` | Optimistic Youth | M | Y | Cheerful, positive | Youth, motivation |
| `Japanese_GenerousIzakayaOwner` | Generous Izakaya Owner | M | A | Friendly, welcoming | Casual, comedy |
| `Japanese_SportyStudent` | Sporty Student | M | Y | Energetic, athletic | Sports, youth |
| `Japanese_InnocentBoy` | Innocent Boy | M | C | Pure, naive | Children's |
| `Japanese_GracefulMaiden` | Graceful Maiden | F | Y | Elegant, gentle | Romance, drama |

### Korean (한국어)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Korean_SweetGirl` | Sweet Girl | F | C | Sweet, adorable | Children's, romance |
| `Korean_CheerfulBoyfriend` | Cheerful Boyfriend | M | Y | Energetic, loving | Romance, dating |
| `Korean_EnchantingSister` | Enchanting Sister | F | A | Charming, captivating | Family, drama |
| `Korean_ShyGirl` | Shy Girl | F | Y | Timid, reserved | Comedy, romance |
| `Korean_ReliableSister` | Reliable Sister | F | A | Trustworthy, dependable | Guidance |
| `Korean_StrictBoss` | Strict Boss | M | A | Authoritative, demanding | Business, drama |
| `Korean_SassyGirl` | Sassy Girl | F | Y | Bold, witty | Comedy, entertainment |
| `Korean_ChildhoodFriendGirl` | Childhood Friend Girl | F | Y | Familiar, friendly | Romance, nostalgia |
| `Korean_PlayboyCharmer` | Playboy Charmer | M | A | Smooth, flirtatious | Romance, entertainment |
| `Korean_ElegantPrincess` | Elegant Princess | F | A | Graceful, royal | Animation, fantasy |
| `Korean_BraveFemaleWarrior` | Brave Female Warrior | F | A | Courageous | Action, fantasy |
| `Korean_BraveYouth` | Brave Youth | M | Y | Heroic | Action, youth |
| `Korean_CalmLady` | Calm Lady | F | A | Composed, serene | Meditation, relaxation |
| `Korean_EnthusiasticTeen` | Enthusiastic Teen | M | Y | Excited, energetic | Youth |
| `Korean_SoothingLady` | Soothing Lady | F | A | Calming, comforting | Relaxation |
| `Korean_IntellectualSenior` | Intellectual Senior | M | E | Wise, knowledgeable | Educational, narration |
| `Korean_LonelyWarrior` | Lonely Warrior | M | A | Solitary, melancholic | Drama, fantasy |
| `Korean_MatureLady` | Mature Lady | F | A | Sophisticated | Professional, drama |
| `Korean_InnocentBoy` | Innocent Boy | M | C | Pure, naive | Children's |
| `Korean_CharmingSister` | Charming Sister | F | A | Attractive, delightful | Family, romance |
| `Korean_AthleticStudent` | Athletic Student | M | Y | Sporty, energetic | Sports, youth |
| `Korean_BraveAdventurer` | Brave Adventurer | M | A | Courageous explorer | Adventure, fantasy |
| `Korean_CalmGentleman` | Calm Gentleman | M | A | Composed, refined | Formal, professional |
| `Korean_WiseElf` | Wise Elf | M | E | Ancient, mystical | Fantasy, narration |
| `Korean_CheerfulCoolJunior` | Cheerful Cool Junior | M | Y | Popular, friendly | Youth, entertainment |
| `Korean_DecisiveQueen` | Decisive Queen | F | A | Commanding | Drama, fantasy |
| `Korean_ColdYoungMan` | Cold Young Man | M | Y | Distant, aloof | Drama, romance |
| `Korean_MysteriousGirl` | Mysterious Girl | F | Y | Enigmatic, secretive | Mystery, drama |
| `Korean_QuirkyGirl` | Quirky Girl | F | Y | Eccentric, unique | Comedy |
| `Korean_ConsiderateSenior` | Considerate Senior | M | E | Thoughtful, caring | Warm, supportive |
| `Korean_CheerfulLittleSister` | Cheerful Little Sister | F | C | Playful, adorable | Family, comedy |
| `Korean_DominantMan` | Dominant Man | M | A | Powerful, commanding | Leadership, action |
| `Korean_AirheadedGirl` | Airheaded Girl | F | Y | Bubbly, spacey | Comedy |
| `Korean_ReliableYouth` | Reliable Youth | M | Y | Trustworthy, dependable | Supportive |
| `Korean_FriendlyBigSister` | Friendly Big Sister | F | A | Warm, protective | Family, support |
| `Korean_GentleBoss` | Gentle Boss | M | A | Kind, understanding | Business |
| `Korean_ColdGirl` | Cold Girl | F | Y | Aloof, distant | Drama, romance |
| `Korean_HaughtyLady` | Haughty Lady | F | A | Arrogant, proud | Drama, comedy |
| `Korean_CharmingElderSister` | Charming Elder Sister | F | A | Graceful | Romance, family |
| `Korean_IntellectualMan` | Intellectual Man | M | A | Smart, knowledgeable | Educational |
| `Korean_CaringWoman` | Caring Woman | F | A | Nurturing | Supportive, warm |
| `Korean_WiseTeacher` | Wise Teacher | M | E | Experienced | Educational |
| `Korean_ConfidentBoss` | Confident Boss | M | A | Self-assured, capable | Business, leadership |
| `Korean_AthleticGirl` | Athletic Girl | F | Y | Sporty, energetic | Sports, fitness |
| `Korean_PossessiveMan` | Possessive Man | M | A | Intense, protective | Romance, drama |
| `Korean_GentleWoman` | Gentle Woman | F | A | Soft-spoken, kind | Calm |
| `Korean_CockyGuy` | Cocky Guy | M | Y | Confident, arrogant | Comedy |
| `Korean_ThoughtfulWoman` | Thoughtful Woman | F | A | Reflective, caring | Drama |
| `Korean_OptimisticYouth` | Optimistic Youth | M | Y | Positive, hopeful | Motivation |

### Spanish (Español)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Spanish_Narrator` | Narrator | M | A | Professional narrator | Documentaries |
| `Spanish_CaptivatingStoryteller` | Captivating Storyteller | M | A | Engaging narrator | Audiobooks |
| `Spanish_WiseScholar` | Wise Scholar | M | A | Knowledgeable | Educational |
| `Spanish_SereneWoman` | Serene Woman | F | A | Calm, peaceful | Relaxation |
| `Spanish_MaturePartner` | Mature Partner | M | A | Sophisticated | Romance, drama |
| `Spanish_ConfidentWoman` | Confident Woman | F | A | Self-assured | Professional |
| `Spanish_DeterminedManager` | Determined Manager | M | A | Ambitious, driven | Business |
| `Spanish_BossyLeader` | Bossy Leader | M | A | Commanding | Leadership |
| `Spanish_ReservedYoungMan` | Reserved Young Man | M | Y | Quiet, introverted | Drama |
| `Spanish_ThoughtfulMan` | Thoughtful Man | M | A | Reflective | Educational |
| `Spanish_RationalMan` | Rational Man | M | A | Logical, analytical | Business |
| `Spanish_Deep-tonedMan` | Deep-toned Man | M | A | Deep, resonant | Commanding |
| `Spanish_Jovialman` | Jovial Man | M | A | Cheerful, friendly | Entertainment |
| `Spanish_Steadymentor` | Steady Mentor | M | A | Reliable mentor | Guidance |
| `Spanish_ReliableMan` | Reliable Man | M | A | Trustworthy | Professional |
| `Spanish_RomanticHusband` | Romantic Husband | M | A | Loving, romantic | Romance |
| `Spanish_Comedian` | Comedian | M | A | Humorous | Comedy |
| `Spanish_Debator` | Debator | M | A | Persuasive | Debate |
| `Spanish_ToughBoss` | Tough Boss | M | A | Harsh, demanding | Business, drama |
| `Spanish_AngryMan` | Angry Man | M | A | Frustrated | Drama, comedy |
| `Spanish_PowerfulSoldier` | Powerful Soldier | M | A | Strong, brave | Action, military |
| `Spanish_PassionateWarrior` | Passionate Warrior | M | A | Fierce, dedicated | Action, fantasy |
| `Spanish_PowerfulVeteran` | Powerful Veteran | M | A | Experienced | Military |
| `Spanish_SensibleManager` | Sensible Manager | M | A | Practical | Business |
| `Spanish_Kind-heartedGirl` | Kind-hearted Girl | F | C | Warm, compassionate | Children's |
| `Spanish_SophisticatedLady` | Sophisticated Lady | F | A | Elegant, refined | Formal |
| `Spanish_FrankLady` | Frank Lady | F | A | Direct, honest | Comedy |
| `Spanish_Fussyhostess` | Fussy Hostess | F | A | Demanding | Comedy, drama |
| `Spanish_Wiselady` | Wise Lady | F | E | Experienced, wise | Guidance |
| `Spanish_ThoughtfulLady` | Thoughtful Lady | F | A | Considerate | Advice |
| `Spanish_AssertiveQueen` | Assertive Queen | F | A | Commanding | Drama, fantasy |
| `Spanish_CaringGirlfriend` | Caring Girlfriend | F | Y | Nurturing | Romance |
| `Spanish_ChattyGirl` | Chatty Girl | F | Y | Talkative, sociable | Comedy |
| `Spanish_CompellingGirl` | Compelling Girl | F | Y | Persuasive | Marketing |
| `Spanish_WhimsicalGirl` | Whimsical Girl | F | C | Playful, imaginative | Children's |
| `Spanish_Intonategirl` | Intonate Girl | F | Y | Musical, melodic | Singing |
| `Spanish_SincereTeen` | Sincere Teen | M | Y | Honest, genuine | Youth |
| `Spanish_Strong-WilledBoy` | Strong-willed Boy | M | Y | Determined | Youth, motivation |
| `Spanish_EnergeticBoy` | Energetic Boy | M | C | Active, lively | Youth, sports |
| `Spanish_StrictBoss` | Strict Boss | M | A | Strict | Business |
| `Spanish_HumorousElder` | Humorous Elder | M | E | Funny | Comedy |
| `Spanish_SereneElder` | Serene Elder | M | E | Calm, peaceful | Meditation |
| `Spanish_SantaClaus` | Santa Claus | M | E | Festive | Holiday |
| `Spanish_Rudolph` | Rudolph | N | C | Reindeer | Holiday |
| `Spanish_Arnold` | Arnold | M | A | Robotic | Sci-fi |
| `Spanish_Ghost` | Ghost | N | A | Spooky | Horror |
| `Spanish_AnimeCharacter` | Anime Character | N | Y | Anime-style | Animation |

### Portuguese (Português)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Portuguese_Narrator` | Narrator | M | A | Professional narrator | Documentaries |
| `Portuguese_CaptivatingStoryteller` | Captivating Storyteller | M | A | Engaging narrator | Audiobooks |
| `Portuguese_WiseScholar` | Wise Scholar | M | A | Knowledgeable | Educational |
| `Portuguese_Deep-VoicedGentleman` | Deep-voiced Gentleman | M | A | Deep, rich | Commanding |
| `Portuguese_ReservedYoungMan` | Reserved Young Man | M | Y | Quiet, introverted | Drama |
| `Portuguese_ThoughtfulMan` | Thoughtful Man | M | A | Reflective | Educational |
| `Portuguese_RationalMan` | Rational Man | M | A | Logical | Business |
| `Portuguese_Jovialman` | Jovial Man | M | A | Cheerful | Entertainment |
| `Portuguese_Steadymentor` | Steady Mentor | M | A | Reliable mentor | Guidance |
| `Portuguese_ReliableMan` | Reliable Man | M | A | Trustworthy | Professional |
| `Portuguese_RomanticHusband` | Romantic Husband | M | A | Loving | Romance |
| `Portuguese_Comedian` | Comedian | M | A | Humorous | Comedy |
| `Portuguese_Debator` | Debator | M | A | Persuasive | Debate |
| `Portuguese_ToughBoss` | Tough Boss | M | A | Demanding | Business |
| `Portuguese_StrictBoss` | Strict Boss | M | A | Strict | Business |
| `Portuguese_AngryMan` | Angry Man | M | A | Frustrated | Drama |
| `Portuguese_Godfather` | Godfather | M | A | Authoritative | Drama |
| `Portuguese_PowerfulSoldier` | Powerful Soldier | M | A | Strong, brave | Action |
| `Portuguese_PowerfulVeteran` | Powerful Veteran | M | A | Experienced | Military |
| `Portuguese_SensibleManager` | Sensible Manager | M | A | Practical | Business |
| `Portuguese_DeterminedManager` | Determined Manager | M | A | Driven | Business |
| `Portuguese_BossyLeader` | Bossy Leader | M | A | Commanding | Leadership |
| `Portuguese_CalmLeader` | Calm Leader | M | A | Composed, steady | Leadership |
| `Portuguese_FascinatingBoy` | Fascinating Boy | M | Y | Charming | Romance |
| `Portuguese_Strong-WilledBoy` | Strong-willed Boy | M | Y | Determined | Youth |
| `Portuguese_EnergeticBoy` | Energetic Boy | M | C | Active, lively | Youth |
| `Portuguese_FragileBoy` | Fragile Boy | M | Y | Sensitive | Drama |
| `Portuguese_MaturePartner` | Mature Partner | M | A | Sophisticated | Romance |
| `Portuguese_HumorousElder` | Humorous Elder | M | E | Funny | Comedy |
| `Portuguese_SereneElder` | Serene Elder | M | E | Calm | Meditation |
| `Portuguese_ConfidentWoman` | Confident Woman | F | A | Self-assured | Professional |
| `Portuguese_SereneWoman` | Serene Woman | F | A | Calm, peaceful | Relaxation |
| `Portuguese_SentimentalLady` | Sentimental Lady | F | A | Emotional | Drama, romance |
| `Portuguese_Wiselady` | Wise Lady | F | E | Wise | Guidance |
| `Portuguese_GorgeousLady` | Gorgeous Lady | F | A | Beautiful | Romance |
| `Portuguese_LovelyLady` | Lovely Lady | F | A | Sweet, endearing | Warm |
| `Portuguese_Pompouslady` | Pompous Lady | F | A | Self-important | Comedy |
| `Portuguese_CharmingQueen` | Charming Queen | F | A | Elegant | Drama, fantasy |
| `Portuguese_AssertiveQueen` | Assertive Queen | F | A | Commanding | Drama, fantasy |
| `Portuguese_CharmingLady` | Charming Lady | F | A | Sophisticated | Professional |
| `Portuguese_InspiringLady` | Inspiring Lady | F | A | Motivating | Motivation |
| `Portuguese_StressedLady` | Stressed Lady | F | A | Anxious | Comedy |
| `Portuguese_FrankLady` | Frank Lady | F | A | Direct, honest | Comedy |
| `Portuguese_Fussyhostess` | Fussy Hostess | F | A | Demanding | Comedy |
| `Portuguese_ThoughtfulLady` | Thoughtful Lady | F | A | Considerate | Advice |
| `Portuguese_GentleTeacher` | Gentle Teacher | F | A | Kind, patient | Educational |
| `Portuguese_Kind-heartedGirl` | Kind-hearted Girl | F | C | Warm | Children's |
| `Portuguese_SweetGirl` | Sweet Girl | F | Y | Sweet, adorable | Romance |
| `Portuguese_AttractiveGirl` | Attractive Girl | F | Y | Charming | Entertainment |
| `Portuguese_PlayfulGirl` | Playful Girl | F | Y | Fun-loving | Comedy |
| `Portuguese_SmartYoungGirl` | Smart Young Girl | F | Y | Intelligent | Educational |
| `Portuguese_UpsetGirl` | Upset Girl | F | Y | Distressed | Drama |
| `Portuguese_ElegantGirl` | Elegant Girl | F | Y | Graceful | Formal |
| `Portuguese_CompellingGirl` | Compelling Girl | F | Y | Persuasive | Marketing |
| `Portuguese_WhimsicalGirl` | Whimsical Girl | F | C | Playful | Children's |
| `Portuguese_ChattyGirl` | Chatty Girl | F | Y | Talkative | Comedy |
| `Portuguese_NaughtySchoolgirl` | Naughty Schoolgirl | F | Y | Mischievous | Comedy |
| `Portuguese_SadTeen` | Sad Teen | F | Y | Melancholic | Drama |
| `Portuguese_CaringGirlfriend` | Caring Girlfriend | F | Y | Nurturing | Romance |
| `Portuguese_FriendlyNeighbor` | Friendly Neighbor | F | A | Warm, helpful | Community |
| `Portuguese_Dramatist` | Dramatist | M | A | Theatrical | Drama |
| `Portuguese_TheatricalActor` | Theatrical Actor | M | A | Dramatic | Entertainment |
| `Portuguese_Conscientiousinstructor` | Conscientious Instructor | M | A | Diligent | Training |
| `Portuguese_PlayfulSpirit` | Playful Spirit | N | C | Cheerful spirit | Fantasy |
| `Portuguese_SantaClaus` | Santa Claus | M | E | Festive | Holiday |
| `Portuguese_Rudolph` | Rudolph | N | C | Reindeer | Holiday |
| `Portuguese_Arnold` | Arnold | M | A | Robotic | Sci-fi |
| `Portuguese_CharmingSanta` | Charming Santa | M | E | Charismatic | Holiday |
| `Portuguese_Grinch` | Grinch | M | A | Mischievous | Comedy |
| `Portuguese_Ghost` | Ghost | N | A | Spooky | Horror |
| `Portuguese_GrimReaper` | Grim Reaper | N | A | Dark, ominous | Horror |

### French (Français)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `French_Male_Speech_New` | Level-Headed Man | M | A | Calm, reasonable | Professional |
| `French_Female_News Anchor` | Patient Female Presenter | F | A | Clear, patient | News |
| `French_CasualMan` | Casual Man | M | A | Relaxed, informal | Casual |
| `French_MovieLeadFemale` | Movie Lead Female | F | A | Dramatic, expressive | Drama |
| `French_FemaleAnchor` | Female Anchor | F | A | Professional anchor | News |

### Indonesian (Bahasa Indonesia)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Indonesian_SweetGirl` | Sweet Girl | F | C | Sweet, adorable | Children's |
| `Indonesian_ReservedYoungMan` | Reserved Young Man | M | Y | Quiet, introverted | Drama |
| `Indonesian_CharmingGirl` | Charming Girl | F | Y | Attractive | Romance |
| `Indonesian_CalmWoman` | Calm Woman | F | A | Composed, peaceful | Relaxation |
| `Indonesian_ConfidentWoman` | Confident Woman | F | A | Self-assured | Professional |
| `Indonesian_CaringMan` | Caring Man | M | A | Nurturing | Family |
| `Indonesian_BossyLeader` | Bossy Leader | M | A | Commanding | Leadership |
| `Indonesian_DeterminedBoy` | Determined Boy | M | Y | Ambitious | Youth |
| `Indonesian_GentleGirl` | Gentle Girl | F | Y | Soft-spoken | Calm |

### German (Deutsch)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `German_FriendlyMan` | Friendly Man | M | A | Warm, approachable | Casual |
| `German_SweetLady` | Sweet Lady | F | A | Pleasant, kind | Warm |
| `German_PlayfulMan` | Playful Man | M | A | Fun-loving | Comedy |

### Russian (Русский)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Russian_HandsomeChildhoodFriend` | Handsome Childhood Friend | M | Y | Charming | Romance |
| `Russian_BrightHeroine` | Bright Queen | F | A | Lively, strong | Drama |
| `Russian_AmbitiousWoman` | Ambitious Woman | F | A | Driven | Professional |
| `Russian_ReliableMan` | Reliable Man | M | A | Trustworthy | Professional |
| `Russian_CrazyQueen` | Crazy Girl | F | Y | Wild, unpredictable | Comedy |
| `Russian_PessimisticGirl` | Pessimistic Girl | F | Y | Gloomy | Comedy |
| `Russian_AttractiveGuy` | Attractive Guy | M | A | Charming | Romance |
| `Russian_Bad-temperedBoy` | Bad-tempered Boy | M | Y | Irritable, grumpy | Comedy |

### Italian (Italiano)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Italian_BraveHeroine` | Brave Heroine | F | A | Courageous | Action |
| `Italian_Narrator` | Narrator | M | A | Professional narrator | Storytelling |
| `Italian_WanderingSorcerer` | Wandering Sorcerer | M | A | Mysterious | Fantasy |
| `Italian_DiligentLeader` | Diligent Leader | M | A | Hardworking | Leadership |

### Arabic (العربية)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Arabic_CalmWoman` | Calm Woman | F | A | Composed | Relaxation |
| `Arabic_FriendlyGuy` | Friendly Guy | M | A | Warm | Casual |

### Turkish (Türkçe)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Turkish_CalmWoman` | Calm Woman | F | A | Composed | Relaxation |
| `Turkish_Trustworthyman` | Trustworthy Man | M | A | Reliable | Professional |

### Ukrainian (Українська)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Ukrainian_CalmWoman` | Calm Woman | F | A | Composed | Relaxation |
| `Ukrainian_WiseScholar` | Wise Scholar | M | A | Knowledgeable | Educational |

### Dutch (Nederlands)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Dutch_kindhearted_girl` | Kind-hearted Girl | F | C | Warm | Children's |
| `Dutch_bossy_leader` | Bossy Leader | M | A | Commanding | Leadership |

### Vietnamese (Tiếng Việt)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Vietnamese_kindhearted_girl` | Kind-hearted Girl | F | C | Warm | Children's |

### Thai (ภาษาไทย)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Thai_male_1_sample8` | Serene Man | M | A | Calm, peaceful | Relaxation |
| `Thai_male_2_sample2` | Friendly Man | M | A | Warm | Casual |
| `Thai_female_1_sample1` | Confident Woman | F | A | Self-assured | Professional |
| `Thai_female_2_sample2` | Energetic Woman | F | A | Active, lively | Motivation |

### Polish (Polski)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Polish_male_1_sample4` | Male Narrator | M | A | Professional | Narration |
| `Polish_male_2_sample3` | Male Anchor | M | A | Professional | News |
| `Polish_female_1_sample1` | Calm Woman | F | A | Composed | Relaxation |
| `Polish_female_2_sample3` | Casual Woman | F | A | Relaxed | Casual |

### Romanian (Română)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `Romanian_male_1_sample2` | Reliable Man | M | A | Trustworthy | Professional |
| `Romanian_male_2_sample1` | Energetic Youth | M | Y | Active, lively | Youth |
| `Romanian_female_1_sample4` | Optimistic Youth | F | Y | Positive | Motivation |
| `Romanian_female_2_sample1` | Gentle Woman | F | A | Soft-spoken | Calm |

### Greek (Ελληνικά)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `greek_male_1a_v1` | Thoughtful Mentor | M | A | Reflective, wise | Guidance |
| `Greek_female_1_sample1` | Gentle Lady | F | A | Soft-spoken | Calm |
| `Greek_female_2_sample3` | Girl Next Door | F | Y | Friendly | Casual |

### Czech (Čeština)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `czech_male_1_v1` | Assured Presenter | M | A | Confident | Presentations |
| `czech_female_5_v7` | Steadfast Narrator | F | A | Reliable | Storytelling |
| `czech_female_2_v2` | Elegant Lady | F | A | Graceful | Formal |

### Finnish (Suomi)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `finnish_male_3_v1` | Upbeat Man | M | A | Cheerful | Motivation |
| `finnish_male_1_v2` | Friendly Boy | M | Y | Warm | Children's |
| `finnish_female_4_v1` | Assertive Woman | F | A | Confident | Professional |

### Hindi (हिन्दी)

| voice_id | Name | G | Age | Description | Best For |
|----------|------|---|-----|-------------|----------|
| `hindi_male_1_v2` | Trustworthy Advisor | M | A | Reliable, wise | Guidance |
| `hindi_female_2_v1` | Tranquil Woman | F | A | Calm, peaceful | Meditation |
| `hindi_female_1_v2` | News Anchor | F | A | Professional | News |

---

## Voice Parameters

### VoiceSetting

```python
from scripts.tts.utils import VoiceSetting

voice = VoiceSetting(
    voice_id="male-qn-qingse",
    speed=1.0,       # 0.5–2.0 (default 1.0)
    volume=1.0,      # 0.1–10.0 (default 1.0)
    pitch=0,         # -12 to +12 (default 0)
    emotion="",      # Leave empty for speech-2.8 auto-matching (recommended)
)
```

### Speed

| Value | Effect |
|-------|--------|
| 0.75 | Slower, deliberate (news, tutorials) |
| 1.0 | Normal pace |
| 1.25 | Slightly faster (energetic) |
| 1.5+ | Fast (time-sensitive) |

### Emotion

| Value | Description | Model Support |
|-------|-------------|---------------|
| *(empty)* | Auto-match from text | speech-2.8 (recommended) |
| `happy` | Cheerful, upbeat | All |
| `sad` | Melancholic, somber | All |
| `angry` | Intense, frustrated | All |
| `fearful` | Anxious, nervous | All |
| `disgusted` | Repulsed | All |
| `surprised` | Astonished | All |
| `calm` | Neutral tone | All |

---

## Custom Voices

### Voice Cloning

Create custom voices from audio samples:
- Source: 10s–5min, mp3/wav/m4a, ≤20MB, clear single speaker
- Best: 30–60s of clean speech with varied intonation

### Voice Design

Generate voices from text descriptions:
- Include: gender, age, vocal characteristics, tone, use case
- Example: "A warm, grandmotherly voice with gentle pacing, perfect for bedtime stories"

Custom voices expire after 7 days if not used with TTS. List all voices: `python scripts/tts/generate_voice.py list-voices`
