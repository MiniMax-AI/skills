# Functional Requirements

Audio, video, notifications, and other functional behavior requirements.

## Audio

### Playback Initialization

| Requirement | Specification |
|-------------|---------------|
| Response time | < 1 second |
| If delayed | Show visual progress indicator |
| User feedback | Immediate acknowledgment of action |

### Audio Focus Rules

| Event | Required Action |
|-------|-----------------|
| Another app requests focus | Pause or reduce volume |
| Focus regained | Resume or restore volume |
| Playback stops | Abandon focus |

### Audio Focus Handling

| Focus Change | Action |
|--------------|--------|
| AUDIOFOCUS_LOSS | Stop playback |
| AUDIOFOCUS_LOSS_TRANSIENT | Pause playback |
| AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK | Reduce volume |
| AUDIOFOCUS_GAIN | Resume playback |

### Background Playback

| Requirement | Implementation |
|-------------|----------------|
| Continue when backgrounded | Use Foreground Service |
| Notification | MediaStyle notification required |
| Media controls | System media controls integration |
| Session | MediaSession for system integration |

## Video

### Picture-in-Picture (PiP)

| Requirement | Specification |
|-------------|---------------|
| Video apps | Should support PiP |
| Aspect ratio | 16:9 to 2.39:1 |
| Auto-enter | When user navigates away during playback |

### Video Encoding

| Standard | Requirement |
|----------|-------------|
| Compression | HEVC (H.265) recommended |
| Fallback | H.264 for compatibility |
| Quality | Adaptive based on network |

### Video Player Requirements

| Feature | Implementation |
|---------|----------------|
| Fullscreen | Support landscape |
| Controls | Play, pause, seek, volume |
| Captions | Support closed captions |
| Resume | Remember playback position |

## Notifications

### Channel Best Practices

| Practice | Reason |
|----------|--------|
| Multiple channels | User can control each type |
| Descriptive names | User understands purpose |
| Appropriate importance | Match user expectation |
| Don't share channels | Different content = different channel |

### Notification Priority

| Importance | Usage |
|------------|-------|
| HIGH | Time-sensitive (messages, calls) |
| DEFAULT | Normal notifications |
| LOW | Background info |
| MIN | Minimal interruption |

### Notification Content Rules

| Do | Don't |
|-----|-------|
| Relevant information | Cross-promotion |
| Clear, concise text | Advertising other products |
| Actionable content | Unnecessary interruptions |
| Set timeouts | Persistent non-ongoing notifications |

### Messaging Apps Requirements

| Feature | Description |
|---------|-------------|
| MessagingStyle | Use for conversation notifications |
| Direct reply | Support inline reply action |
| Conversation shortcuts | Enable direct share |
| Bubbles | Support floating conversations |

### Notification Grouping

Group related notifications together with a summary notification. Set appropriate group keys and summary flags.

## Sharing

### Android Sharesheet

Use the system sharesheet for sharing content. Create an ACTION_SEND intent with appropriate type and extras, then use createChooser().

### Direct Share

Provide conversation shortcuts for Direct Share ranking:
- Create ShortcutInfo for each conversation
- Set appropriate categories
- Push dynamic shortcuts

## Background Services

### Service Restrictions

| Rule | Implementation |
|------|----------------|
| Avoid long-running services | Use WorkManager |
| No background starts (API 26+) | Use foreground service or JobScheduler |
| Battery-efficient | Batch work, respect Doze |

### Poor Background Service Uses

| Don't Use For | Alternative |
|---------------|-------------|
| Maintaining network connection | FCM (push notifications) |
| Persistent Bluetooth | Companion device manager |
| Keeping GPS on | Geofencing, fused location |
| Polling server | FCM or WorkManager |

## State Management

### State Preservation Requirements

| Scenario | Required Behavior |
|----------|-------------------|
| App switcher return | Exact previous state |
| Device wake | Exact previous state |
| Process death | Restore critical state |
| Configuration change | Seamless transition |

### State Categories

| State Type | Storage |
|------------|---------|
| UI state (scroll, selection) | ViewModel + SavedState |
| User input (forms) | SavedState |
| Navigation | NavController state |
| Persistent data | Room database |

## Navigation

### Back Button/Gesture

| Requirement | Implementation |
|-------------|----------------|
| System back | Navigate to previous screen |
| Gesture navigation | Support back gesture |
| No custom back buttons | Use system navigation |
| Predictable | User knows what back does |

## Gestures

### Gesture Navigation Support

| Gesture | Default Action |
|---------|----------------|
| Swipe from left edge | Back |
| Swipe up from bottom | Home |
| Swipe up and hold | Recent apps |

### Custom Gestures

| Practice | Reason |
|----------|--------|
| Avoid edge swipes | Conflicts with navigation |
| Provide alternatives | Not all users gesture-capable |
| Test with gesture nav | Ensure no conflicts |

Handle system gesture insets to avoid conflicts with edge gestures.

## Functional Checklist

### Audio
- [ ] Playback starts within 1 second
- [ ] Audio focus requested and released
- [ ] Responds to focus changes (duck/pause)
- [ ] Background playback with notification
- [ ] MediaSession integration

### Video
- [ ] Picture-in-picture supported
- [ ] HEVC encoding used
- [ ] Playback position remembered
- [ ] Captions supported

### Notifications
- [ ] Appropriate channels defined
- [ ] Correct importance levels
- [ ] No promotional content
- [ ] Grouped when appropriate
- [ ] Timeouts set where applicable

### Messaging (if applicable)
- [ ] MessagingStyle used
- [ ] Direct reply supported
- [ ] Conversation shortcuts
- [ ] Bubbles supported

### Background
- [ ] WorkManager for background work
- [ ] No long-running services
- [ ] Battery-efficient design

### Navigation
- [ ] Standard back behavior
- [ ] Gesture navigation supported
- [ ] State preserved across lifecycle
