# pgr 冷知识 (?

- 谱面游玩的 `drag&hold` 有效触控点上限为 `20` (待验证)

- 大部分故事板由 `levelMod` 实现, 例如:

  ```json
  {
    "levelMods": [
        "LevelMod/Introduction",
        "LevelMod/LuminescenceLevelEffect",
        "LevelMod/ChallengeModeLevelMod",
        "LevelMod/TheChariotLevelEffect",
        "LevelMod/Destruction321LevelEffect",
        "LevelMod/DFLevelEffect",
        "LevelMod/HPDisplay",
        "LevelMod/RetributionEffectSecondPhase",
        "LevelMod/RrharilEventEnter",
        "LevelMod/100UiChange",
        "LevelMod/001UiChange",
        "LevelMod/RetributionEffect"
    ]
  }
  ```

  tip: `100UiChange` 与 `001UiChange` 冲突, 会随机加载其中一个
