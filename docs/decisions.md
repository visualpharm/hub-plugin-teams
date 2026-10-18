# Decisions

## 2026-10-15 · Offline source gate
Decided: retain the existing mocked Python and Node checks under one reviewed local
argv gate. Require the core dependency through PYTHONPATH or HUB_CORE.
Why: a plugin source change must be checkable without reading real accounts or
starting its collector. Undo: remove the wrapper and use the documented commands.
By: agent, within the authorized Inbox source adaptation.

## 2026-10-15 · Explicit core task relationship
Decided: feature-detect the shared body/decision helpers and accept only an explicit
task_id matching a real core snapshot item before showing task actions. Source prose
never supplies an identity. Keep existing reply/delivery controls and older-hub text.
Why: Inbox and core task IDs represent different state; guessed associations can
complete unrelated work. Queue/error/closure stays in the existing message context.
Undo: remove the web adapter; no channel migration or collector change.
By: agent, within the authorized task-flow scope. Installation remains held.

## 2026-10-15 · False closure and mixed history correction
Decided: unread-source disappearance never supplies an owner reply timestamp. Keep
actual Teams reply facts, successful-send receipts, explicit dismissals and newer
message supersession. Add an operator correction referencing the exact original
message and false closure, accepted only via the owner or the plugin's own process.
Recheck current accepted feed and stored destination before changing the projection;
successful sends, later closures, superseded sources and missing evidence refuse.
Why: reading, filtering, source errors and restarts can remove unread markers.
Reposting a message loses its original post/draft identity. Corrections retain all
raw posts, original source and drafts, and invalidate contaminated derived history.
WhatsApp history validates expected channel/account/peer, raw peer-qualified row ID
and dated per-row provenance before publishing any row. Missing expected account or
legacy provenance fails closed. This is identity consistency, not a signed source.
Undo: revert this source change; never delete correction or original journal posts.
By: agent, within the authorized Inbox repair; runtime activation and rendered
acceptance remain held pending coordinated producer, web and native adoption.

## 2026-10-15 · One Inbox suggestion contract across assistant request paths
Decided: retain the selected server's canonical Hub route, plugin authorship and existing raw reply-to-post
format. Share owner cfg.prompt and verified-context/one-next-action guidance across automatic, manual draft
and work request builders. A leading separator permits private context without inventing recipient text.
Keep recipient approval and source/identity restrictions; do not force browser/source fallbacks for a draft.
Why: manual requests previously omitted the owner's instructions, and one-phrase Why did not explain what to do.
Undo: revert this prompt/helper change; no source state, credential, recipient or client schema migration.
These are source instructions and parser fixtures, not proof of actual model output, result-generation
authentication, native acceptance or release. Native owners retain response/hub/thread/edit protection.
By: agent within the existing Inbox producer task; install/activation remains separately coordinated.

## 2026-10-15 · Routine authority and current-version delivery
Decided: routine correspondence within established delegated authority may proceed
without repeated approval; owner presence/inactivity never adds authority. Preserve
money/legal/health/infrastructure/strategic and owner-information decisions. This
supersedes the previous blanket recipient-approval wording for routine handling.
Technical choice: existing collector owns one durable manual/auto claim, explicit
editor holds, source preflight and actual transport receipts. Private revisions
return authenticated explicit-Apply proposals. Whole requests preserve exact private
text and report canonical coverage limits. See inbox-management.md for the wire.
Why: prompt-only approval and client-local versions cannot prevent duplicate sends
or unsafe late editor replacement. Unknown outcomes cannot authorize retries.
Undo: revert candidate source while preserving journal/claim history; do not clear
uncertainty or enable an older automatic path. By: agent within authorized scope.
Source is not installed; all-client adoption and coordinated activation remain required.

## 2026-10-15 · Rejection replay and complete guidance
Decided: persist pre-submission rejection disposition, so journal replay cannot
turn a previously rejected request into a new send. Publish complete exact triage
guidance through bounded hashed chunks independently of the legacy settings size.
Why: transport recovery must not resurrect old actions, and truncated/stale owner
guidance cannot govern automated replies. Undo: revert source without deleting
request, claim or instruction history. By: agent within the same authorized slice.

## 2026-10-15 — Web Inbox uses the shared composer and collector confirmations

The web consumer reuses the page composer only when composerTransport:1 is advertised.
The existing node/focus/set facade remains intact. Provider submission uses an explicit callback;
it never falls through to a session send. New collector-protocol editors require an acknowledged
current hold, private revision stays source/request/editor-bound, and Apply remains local and explicit.
Serialized envelopes are bounded before the 2000-character feed limit can truncate them.
Queued and uncertain submissions retain drafts; a matching actual receipt closes the editor.
Conversation grouping follows contact/box identity and never guesses from a repeated name.
Unsupported guarded adapters and attachments remain held under the collector contract.
Undo: revert this web consumer slice; it changes no collector policy, account or journal schema.
Installation and live acceptance require the existing scoped integration safe point.

## 2026-10-15 — Acquire web editor holds on owner input
A reply preview or generated fill alone does not acquire a hold. The first actual
reply/private-instruction edit does, including intentional empty edits. Existing
holds persist through navigation; provider delivery still requires the matching
collector receipt.

## 2026-10-15 · Conversation-scoped editor holds
Decided: retain editor holders and edit revision once per verified source-account/conversation
identity in the existing collector state. New and existing source rows share that exclusion;
source version and delivery claim remain bound to the exact current item and conversation facts.
Final claim rechecks after preflight, and an explicit matching-client manual Send consumes
the hold and stores its claim atomically, independently of automatic-policy activation.
Why: row-only holds let a new incoming row race the client's next poll and automatic delivery.
Migration preserves all legacy holders; conflicts require each holder's explicit CAS release.
Account/destination changes neither import a different identity's hold nor delete its original hold.
Undo: reconcile active conversation holds before reverting; old row-only code cannot enforce them.
By: agent within the existing shared-editor race correction.

## 2026-10-15 · Manual follow-up source lifecycle
Decided: a verified successful collector send advances the conversation version from its
actual Graph receipt and normalized outgoing body, issuing a fresh token with additive
manual_followup capability. Deliberate current-token/editor sends may continue the selected
closed conversation; automatic work still requires a current open incoming source.
Verify the latest own receipt/body/account and absence of newer source facts before each
follow-up claim. Unknown delivery creates no next version or permission to retry.
Why: keeping only an incoming source version blocks legitimate additional replies, while
loosening its old claim could duplicate work or misattribute an earlier receipt.
Only exact prior source/payload matches return duplicate receipts; identical completed
request replay returns persisted evidence without resending. Clients never invent tokens.
Undo: settle pending claims and coordinate client downgrade; retained receipt/source
evidence stays in collector state, and unanchored legacy sends are never silently upgraded.
By: agent within the existing native manual-reply compatibility requirement.

## 2026-10-15 · Native compatibility evidence binding
Decided: retain source-derived synthetic native wire fixtures with immutable source
revisions and file hashes; test their requests through the real producer parser and
collector, including native omission of additive token metadata.
Why: a historical native source checkpoint cannot certify later receipt semantics
or replace native execution and UI acceptance. Keep known consumer gaps explicit.
Undo: update fixture provenance after reviewing a new native source revision; do not
relabel old artifacts or broaden their acceptance scope. By: agent.

## 2026-10-17 — Inbox panes follow available width
The conversation list collapses when its content container is at most 900px, keeping the selected conversation and shared reply composer full width. The split layout requires 336px for the list and at least560px for reading. Browser regression covers390,768,834,1024,1280,1440px; current collector changes are retained.

## 2026-10-17 — Native Inbox action placement
Conversation actions now precede the shared reply field, ordered Hide, Draft, Work. Source destination is an accessible icon in the conversation header. Native SF Regular assets are reused; narrow detail panes retain44px targets with accessible labels. Reaction support is a separate missing web action and remains open. Explicit private revision and Close editor retain their collector semantics. Verified165Pythoncases plusNodecontracts; seveneditorjourneys separately inlight/dark withactual color-scheme assertions.


## 2026-10-17 — Native Inbox reactions in the web action row
The shared web action row now exposes the native six-reaction picker. Posting is pending until the collector reports the exact message and request; refusal permits a new request and never clears the unsent reply. Reload replays the latest reaction receipt. The existing collector decides delivery and moves the source to Done. Verified 166 Python cases, all Node contracts, pointer targets at 360/390/1240 and light/dark captures.

## 2026-10-17 — Exact conversation history
Opening a reply-capable conversation requests its collector history without marking the upstream conversation read. Earlier messages appear on explicit reveal; complete chunks are joined in chronological order and older-page retries retain the same source/cursor. Late responses remain bound to their source, and refresh preserves the reading position and reply. Chat messages use incoming/outgoing bubbles; email retains its document presentation. Verified 173 Python cases plus Node contracts, with six native-fixture media captures at phone/tablet/desktop in both themes. Playback, historical message actions, and full native parity remain separate open checks. Deployment is local to the private tailnet; public push is held pending explicit destination approval.

## 2026-10-17 — Native conversation sorting
Inbox defaults to importance, using the highest-ranked open message in each exact conversation and native verdict/urgency/risk weights; equal priority retains newest-first order. Time is an explicit persisted alternative. Rank-feed failure preserves the list and offers Retry. The sort menu reuses the native Icons8 asset, keeps 44px targets, dismisses with Escape/outside focus, and preserves folders/search/drafts. Verified174Python plus Node contracts and four rendered menu sizes. Ivan explicitly approved publishing these Inbox fixes to the existing public visualpharm/hub-plugin-teams fork; the verified branch through3655926 was pushed and remote SHA confirmed. The earlier hold is resolved for this destination.


### 2026-10-17 — Чтение переписки как в нативном клиенте
Короткая история прижата к действиям и полю ответа; длинная остаётся прокручиваемой, позиция чтения сохраняется. Пояснение черновика стоит перед действиями и не попадает в отправку. Ссылки исходящих пузырей наследуют контрастный цвет текста; файлы используют акцент хаба вместо браузерного синего/фиолетового подчёркивания. Две воспроизведённые визуальные регрессии, полный gate175Python+Node и три проверки после последней правки ссылок зелёные.


### 2026-10-17 — Одна шапка переписки
При узкой области чтения переписка использует собственную шапку с именем и возвратом к Inbox. Переход назад не закрывает редактор и не теряет текст. Частные инструкции и освобождение редактора остаются в меню черновика, без лишней строки под ответом. У широкого списка сохраняется общая навигация.176Python+Node зелёные; четыре сценария навигации/CAS и финальная проверка значка;8 итоговых нативных парных кадров.

### 2026-10-17 — Черновик переживает перезагрузку
Текст владельца хранится в браузере для точного источника, аккаунта/переписки и входящего сообщения. Квитанция принятой отправки очищает только связанный с ней черновик: более новая правка сохраняется и остаётся доступной. Перезагрузка не отправляет текст и не захватывает редактор. Если браузер запрещает хранение, текст остаётся на странице с явным предупреждением.

### 2026-10-17 — Одно намеренное нажатие отправки
Отправка и пересмотр черновика ждут подтверждения текущего редактора, а не требуют второго клика. Ожидание ограничено десятью секундами; смена текста, источника, закрытие или уход из переписки отменяют продолжение. Отказ не отправляет текст. При новой правке во время ожидания сохраняются оба неотправленных фрагмента, как в общем композере, в том числе после перезагрузки. Пять новых сценариев покрывают первый клик, нетронутый совет, отказ, правку и возврат к списку; полный gate184Python+Node зелёный.

### 2026-10-17 — Нативные действия переписки
История запрашивается кнопкой «Показать более ранние», а не при открытии; загрузка, отказ и повтор остаются явными. Локальное удаление черновика доступно внутри общего поля на ядре с composerActions, на старом ядре — в меню. Очистка переживает перезагрузку и ничего не отправляет. Значки удаления и отправки взяты без изменений из нативного набора; шапка, источник, день, время сообщения и пояснение согласованы с текущими кадрами. Полный прогон186 выявил одну гонку готовности в проверке истории; после исправления пять затронутых сценариев и все Node-контракты зелёные. Восемь кадров phone/desktop в обеих темах просмотрены выборочно. QuickSend, действия над историческими сообщениями и полная медиа-паритетность остаются открытыми.

### 2026-10-17 — Входящее не останавливает проигрывание
Обновление Inbox сохраняет подключённые медиа-узлы открытой переписки. Воспроизведение ранее сбрасывалось на ноль при входящем от другого человека. Нативная фикстура с настоящими WAV/MP4 воспроизводит оба плеера клавиатурой и проверяет сохранение аудио/позиции при обновлении. Полный187 прогон обнаружил три регрессии в первом варианте обновления текста; все три исправлены и перепроверены, обычный новый сценарий и все Node-контракты зелёные. Восемь свежих кадров и проигрывание прошли12.08s; горизонтальное переполнение истории равно0. Полная визуальная идентичность медиа ещё не достигнута.

### 2026-10-17 — Контекст нативной переписки
Веб показывает исходную цитату, полученные реакции, отметки пересылки/правки и аккаунт источника. Текст цитаты создаётся только как текст, не как HTML. Исходящие пузыри Inbox используют нативный зелёный; файлы — исходный значок документа, имя и размер. Выбранная переписка помечается aria-current. Четыре затронутых сценария, отдельная проверка источника/выбора и все Node-контракты зелёные; восемь свежих кадров и проигрывание проверены на неизменённой нативной фикстуре. Нативный аудиоплеер, превью ссылок, QuickSend и вложения ещё в работе.

### 2026-10-17 — Превью ссылок как в нативной истории
Карточка ссылки использует существующий /api/linkpreview с защитой сети на сервере и ограниченным клиентским кешем. Адрес перехода берётся из исходного сообщения, а не из ответа сервиса; заголовок/сайт остаются текстом, опасные URL изображений не вставляются. Карточка не заменяет узел проигрывания и сохраняет нижний край истории при загрузке. Четыре затронутых браузерных сценария и все Node-контракты зелёные; четыре кадра в двух темах и фактическое проигрывание прошли7.69s.

### 2026-10-17 — Поле ответа в одну строку
Слот локального удаления переносил даже пустое поле Inbox в две строки (90px вместо46px). В Inbox удаление и отправка теперь занимают одну строку с текстом; запись голоса сохраняет отдельную полосу. Сценарий воспроизводит лишнюю строку до исправления, затем проверяет360/402/834/1240px, пустой и заполненный ответ, отсутствие перекрытий. Он и сценарии очистки/первой отправки зелёные7.24s.

### 2026-10-17 — Нативный голосовой пузырь
Голосовое использует исходные значки play/pause, круг32px с целью44px, шкалу и длительность; расшифровка внутри того же пузыря. Ошибка видна, повтор заново загружает источник. Подключённый плеер сохраняется при обновлении; второй плеер останавливает первый. Реальные WAV/MP4 прошли воспроизведение/паузу, клавиатурную перемотку и непрерывность при входящем, четыре кадра просмотрены. Нативный mock отдавал seekable=[0,0]; веб-адаптер теста теперь сохраняет его байты, но использует Range-транспорт живого сервера. После этого seekable=[0,6], перемотка подтверждена. Три обычных браузерных сценария, отдельный отказ и Node-контракты зелёные.

### 2026-10-17 — Полный контрольный прогон
8156992:192Python-теста106.73s и все Node-контракты зелёные. При интеграции отдельного среза высота44px иногда измерялась43.9997px; проверка сортировки допускает0.01px погрешности дробной геометрии, сохраняя44px CSS-цель. Правило частой публикации после затронутых проверок записано и в CLAUDE.md плагина.

### 2026-10-17 — Протокол редактора определяется источником
Глобальный inbox_protocol.version=1 ошибочно создавал CAS-редактор и для WhatsApp/Telegram/email без inbox-токена: обычный ответ блокировался. Явный токен любого сообщения по-прежнему включает защиту; Teams и неизвестный источник при объявленном CAS остаются закрыты без токена. Только три известных внешних канала без токена используют обычный транспорт и его подтверждение. Сборщик не менялся. Три внешних канала воспроизводили дефект; четыре браузерных проверки28.624s и все Node-контракты зелёные, включая отказ Teams без токена и несовпадающее подтверждение. Проверены видимое закрытие редактора и извлечение принятого ответа из Sent, а не отсутствие скрытого старого DOM.

### 2026-10-17 — Быстрое сообщение хабу из Inbox
Молния открывает общее поле хаба, не меняя переписку и её ответ. Собственный текст сохраняется по хабу в localStorage, закрытие/перезагрузка не отправляют его. Только принятая отправка очищает этот текст; отказ оставляет диалог и текст. Активную запись нельзя скрыть закрытием. Сценарии проверяют точного адресата, одну отправку, независимость двух черновиков, отказ и Escape;3 затронутых16.11s, финальные2 —9.91s. Четыре кадра360/402/834/1240 с проверкой фактической темы просмотрены. Исправление общего поля b04ed1f нужно для переноса уже введённого текста при сужении. Полная визуальная идентичность маленькому окну Mac ещё открыта; первый проход реализует действие и сохранность данных.


### 2026-10-17 — Web Inbox file replies use the existing source transport
Enable attachments only for modern WhatsApp, Telegram and email messages without an explicit guarded token, and only when the core advertises composerFiles. Teams/CAS remains text-only; collector code and file-path containment checks are unchanged. Uploaded metadata is saved with the exact origin/source/conversation/message draft until a matching receipt, and the shared input uses that identity rather than only message id. Refusals retain the caption and exact file; file-only replies work, and Discard clears both. Synthetic raw uploads, three sources, reload, cross-source isolation, late refusal/retry and discard are checked before publication.


### 2026-10-17 — QuickSend owns its uploaded draft and preserves later edits
The Inbox QuickSend dialog persists uploaded metadata beside its origin/Hub-scoped text. Queue acceptance clears only the submitted draft: if a later text or upload is already in the composer, keep it and leave the dialog open. Reload restores an uploaded file; file-only sends target the Hub, never the Inbox recipient. Recording uses the shared composer and cannot be hidden by Close; cancel produces no send. Synthetic file and pending-request regressions reproduced both former losses; recording/cancel is exercised with a generated browser audio stream, not a real microphone.


### 2026-10-17 — Native New message on the web
Use the existing contacts/send_new collector contract, preserving its opaque recipient key and rid. Search responses bind to exact query/rid; user content is text, never HTML. New-message draft is origin+Hub scoped and survives close/reload, separately from replies and QuickSend. A collector refusal permits a new explicit attempt; unknown HTTP acknowledgement retries the SAME id, never invents delivery. Exact rid+recipient receipt closes only the unchanged sent draft, retaining newer edits. Actual synthetic browser checks cover email subject, source selection, refusal/reload/retry, stale search/receipt, duplicate submit, unknown acknowledgement, Escape and four rendered widths/themes. Collector/provider code is unchanged.


### 2026-10-17 — Interrupted new-message delivery stays bound to its original payload
Hostile source review exposed two reproduced browser failures: a never-settling send stayed disabled after reload, and Enter in contact search submitted the form. Recovery now reuses the original rid, locks the recipient until a receipt, and displays the original message when retrying; later edits are retained. Missing receipts time out to explicit recovery, without automatic sends. Storage failures are visible and search results are announced. The collector reservation-without-outcome crash case is owned separately; web does not invent successful delivery.


### 2026-10-17 — Unschedule and uncertain delivery receipts
The web exposes native Unschedule for deferred replies and waits for the exact collector receipt. Newer unsent text survives cancellation and reload; the guarded editor resumes with the collector-provided hold token. Wrong-source receipts do nothing. Unknown new-message outcomes from the collector remain pending and can only replay the original id; they never become an automatic new attempt. Provider and collector code are unchanged in this slice.


### 2026-10-17 — Outgoing chat replies follow native bubbles
Match the inspected native Inbox sentBubble layout: non-email replies are green, right aligned, with delivery state and Unschedule below. Mail keeps its letter panel. Local sends are attributed to the owner immediately, before the feed echoes them; automatic Hub replies remain distinct. Reuse byte-identical Icons8 SF Regular clock/warning/double-tick assets from native0597a826 at16px. Native fixture comparison still has separate open geometry/keyboard coverage; this slice does not claim full pixel parity.
The failure bubble uses a darker red (#b42318) for readable white text; its status uses normal foreground as native does, avoiding small red error prose. This is an explicit contrast adjustment, not a pixel-identity claim.

### 2026-10-17 — Delivery recovery never changes recipients or invents failure
Hostile review reproduced a canceled payload being restored under a newly rebound contact. Detach outstanding deliveries when the exact source binding changes, retain the original stored draft, and ignore subsequent receipts for those detached request IDs. Collector outcomes marked unresolved remain unresolved in both ordinary and guarded editors; they cannot enable a new send. Cancellation timeouts follow the request attempt across repeated scheduled facts instead of comparing replaced row objects. Browser regressions reproduce each failure; the rebound-draft test also checks the published previous source in isolation. Receipt-less reply recovery still needs collector outcome replay and is tracked separately; no unsafe new-ID retry is introduced.

### 2026-10-17 — Suggested drafts obey the same pending-send boundary
A different Hub suggestion exposed the legacy Send action after closing the shared composer, allowing another request while the first awaited confirmation. All entry points now share the pending predicate; the suggestion stays editable but its Send action waits. A definitive refusal re-enables an explicit new send. The browser regression failed before the fix and verifies both blocked pending delivery and the allowed retry after refusal.

### 2026-10-17 — Suggested reply acknowledgment loss preserves uncertainty
The legacy suggested-reply path now retains an unresolved delivery after a failed web acknowledgment, consistent with the shared composer. A request may already have reached the collector; only its receipt can establish delivery or definitive refusal. Keep the original draft and rid, suppress another suggested send, and preserve any collector outcome received before the HTTP response. No new retry protocol or collector change is introduced.


### 2026-10-17 — Exact-message native menu
Current and historical Inbox rows expose Copy, Hand This Message to Hub, and Draft Reply to This Message through right click, long press or the keyboard context-menu key. History retains its trusted collector post and chunk location; draft requests carry the exact provider turn, sender and timestamp through the native ask protocol. Work prefills the shared Hub composer and does not send or mark the conversation completed. Open menus are invalidated when the source binding changes; copied text and existing reply drafts remain separate. Native Icons8 assets and shared menu tokens are reused. Seven widths in both themes are inspected; this is scoped menu coverage, not full native pixel parity or actual Safari long-press verification.


### 2026-10-17 — Message menu review follow-through
A second touch gesture dismissed the old menu after arming the new timer, canceling it. Dismiss in capture phase before the row listener. Restore keyboard focus to the current row after a flat-list refresh, or to the prior connected control; Tab and stale-menu dismissal use the same restoration. Historical Work now names the trusted thread post and provider turn instead of attributing historical text to the latest message post. This corrects a native behavior too: exact-message identity takes precedence over copying that defect. Copy uses displayed message text and omits media placeholders. Four real-browser regressions failed before these changes and all eight menu scenarios pass afterward.


### 2026-10-17 — Browser fixtures consume only observed action facts
The Inbox browser fixture now deletes only paths returned by its spool snapshot.
An atomic writer's temporary file and facts arriving later remain untouched.
A deterministic regression reproduces the old deletion and checks both kinds
of retained work. This repairs a full-gate race without editing frozen core,
collector behavior, or any user-facing delivery assertion.


### 2026-10-17 — Conversation pins remain a local preference
Conversation options now expose Pin/Unpin. Pins are scoped by browser origin,
Hub name, source and stable conversation identity, survive reload, and sort
matching conversations first without bypassing search or folder filters.
Pinning never sends a provider action or changes read/delivery state. Storage
refusal leaves the displayed pin unchanged and preserves the reply draft.
Menu open state and keyboard focus survive feed refreshes. The native pin asset
is unchanged; synthetic phone and desktop frames verify its rendering, not
cross-device synchronization or complete native pixel parity.


### 2026-10-17 — Pin state across already-open tabs
Read the current serialized preference before a pin mutation and refresh visible
rows on storage events. Two open tabs must not overwrite each other's sequential
pin changes. Conversation options use their own semantic class, sharing only CSS
presentation with editor options so existing editor controls keep exact ownership.

Teams channel roots and mentions share the same collector conversation contact,
so their pins use one Teams family identity. Existing category pins migrate when
read. Corrupt or unreadable preference values are never overwritten by a toggle.
Flat cards restore focus by exact visible message/card identity. Tab closes the
menu consistently with sibling controls. Hub renames remain a separate scope
migration question; the current key follows the existing Hub-name convention.


### 2026-10-17 — Local unread reminders preserve the reply
Conversation options expose Mark unread and return to the conversation list with
the exact reply retained. The local reminder survives reload and takes precedence
over a provider-read flag, without changing that provider state. Opening clears
only the local reminder. New records bind the Hub, source conversation and inbound
message; old seen IDs remain a read-only compatibility fallback. Writes re-read
storage, refuse corrupt/unreadable state, and retain the old value on quota failure.
Parsed state is cached by its exact serialized value so row rendering does not
parse the full preference repeatedly. No provider read operation was added; that
explicit action requires its separate receipt-aware workflow.


### 2026-10-17 — Read preference failures stay visible
Opening a conversation surfaces a failed local read write, leaves the reminder
unchanged, and keeps the editor usable. A successful retry clears that error.
Empty targets cannot report a saved reminder. Read preferences refuse growth
beyond 256 Ki characters per Hub, without deleting old reminders, to limit their
share of origin storage. This is a bounded stop, not a guarantee of free browser
quota; compaction and stable Hub rename migration remain separate work.


## 2026-10-17: Explicit provider read receipts
Conversation options offer provider Mark read only for Telegram, WhatsApp and Mail messages with an exact target fingerprint. Opening a conversation and Mark unread remain local. Persist the original request before sending; after a lost acknowledgement, Check read status reuses that rid. Only a trusted matching id/target/rid receipt confirms success. Provider failure and unknown outcomes do not silently start another operation; the owner can inspect the original conversation. Storage refusal sends nothing and retains drafts. Keep the existing legacy native receipt compatibility path separate from modern target-bound proof.

## 2026-10-17: Reply persistence is an admission requirement
Both shared and legacy reply composers must save the pending request id and draft before posting a send. A quota/privacy refusal keeps text and uploaded files in the current page, displays a recoverable error, and sends nothing. Release only the unsent local editor claim, never a request already posted. Retrying after storage recovery persists a new request before transport; existing unknown-outcome handling remains unchanged. This closes the gap where a draft warning appeared but the provider request still escaped.

## 2026-10-17: Scheduling and unresolved reply admission
Send options expose Send now and an explicit future date. A scheduled request keeps the selected instant and uses the existing collector scheduling/cancellation protocol; queue acceptance never reports delivery. An empty or invalid scheduling attempt cannot arm a later ordinary send. The optional composerTrailing capability places options after Send; older composers receive the same control through leading. This is a partial native menu: remembered Send and Archive, recipient working-hour shortcuts and weekend exceptions remain separate work.

Pending replies now have a separate persisted record containing the exact request, scoped to Hub, source, conversation, message and available target fingerprint. Editing the draft cannot erase it. Reload restores the pending guard and prevents a new request until a matching trusted terminal receipt settles the original. Browser Web Locks serialize admission and settlement across tabs. No automatic replay or new-rid retry is offered for an unknown outcome; provider replay retention must be verified before exposing recovery. Existing records from before this change cannot recover request details that were never saved.


## 2026-10-17 — Bind reply requests and receipts to the observed conversation

Modern message facts carry the collector target fingerprint. Shared, guarded and legacy reply composers now return that exact target, persist it with the original request, and retain it in restored delivery state. A trusted delivery fact with the right rid but a missing or different target must not mutate the editor, clear pending storage, or acknowledge success. Filtering occurs before editor reconciliation. Legacy targetless requests remain compatible. This consumes the independently verified installed collector target contract; it does not automatically replay uncertain requests or alter the collector.


## 2026-10-17 — Keep delivery confirmation feedback in Inbox
The shared composer retains transport errors until its next submission. Pending delivery and lost acknowledgement are instead represented by Inbox-owned feedback, so the matching receipt can clear them without destroying the active editor or upload. The original durable request still blocks replacement sends. The shared completion callback restores the latest draft and files, and its short acknowledgement says only that the reply is retained. Successful guarded receipts also clear obsolete editor errors. No new core API is needed; frozen composers use the same behavior.

Owner send echoes from another client may have no browser pending record. Their matching terminal receipt clears only Inbox-owned feedback once no reply remains pending. A draft-save warning takes precedence over a pending-delivery notice and survives receipt reconciliation. Idle editors ignore rid-less history/media facts before dereferencing delivery state.


## 2026-10-17 — Explicit original reply recovery
Only a trusted collector config with reply_replay:1 enables Retry original reply. The action requires a durable request matching the current Hub, source, conversation, message, target and guarded version. It reuses the exact original payload and rid, never the newer draft, and never runs automatically. It may first-submit a request lost before Hub admission, so its label does not imply a read-only status check. Collector idempotency supplies provider safety; timeout and transport refusal retain the original pending request. Only a matching terminal receipt settles it. Repeated clicks coalesce while transport is pending. Mismatched guarded replay versions are rejected before rendering a sent state or mutating the editor. Older collectors and corrupt/targetless records remain blocked.

Successful replay receipts use the same draft and answered-state cleanup as fresh success. A delivery observed after the editor closes must still clear its exact pendingRid draft tombstone. An unchanged external composer is cleared; newer edits/files remain. A rendered sent bubble alone is not settlement acceptance.

## 2026-10-18 — Schedule at the recipient's next working start
The Inbox send menu reads working hours only from trusted collector config. Resolve the next strictly future opening in the Hub's IANA timezone, falling back only to its explicit UTC offset; apply the exact contact's weekend exception. Display the instant in the device timezone and recalculate on click before using the existing durable scheduling path. Invalid or missing hours hides the shortcut. DST gaps advance by the transition duration; overlaps select the first future matching occurrence. No automatic send, recipient-settings mutation, or device-zone assumption is introduced. Remembered Send and Archive and the weekend setting control remain separate work.


## 2026-10-18 — Reactions bind the original destination
A modern reaction carries the message target through the collector parser, provider preflight and receipt. The web only confirms its exact request/id/target; missing or wrong target receipts cannot paint success. Rebinding a message detaches its old reaction, and a detached button cannot act on a replacement conversation. Preserve local pending ownership across owner echoes and retain legacy targetless replay behavior. Drafts remain independent. This follows the reply identity boundary and does not add automatic replay or provider sends from navigation.

Target-bearing messages require the collector-owned reaction_target:1 capability before reactions are enabled. A missing/revoked capability blocks both the visible trigger and detached controls; receipts for already admitted requests still settle normally. Old targetless collectors retain their legacy behavior. This avoids assuming that a collector emitting message targets also preserves them in reaction requests.

## 2026-10-18 · Recipient weekend settings
Decided: Expose the native weekend option only with trusted hours_for_bound:1, valid Hub working hours, and an exact message/contact/target. The checkmark follows collector config. Retain the original setting request in Hub/contact-scoped storage with the immutable original message and target before transport; explicit retry reuses it and a matching collector receipt alone settles it. Receipts never overwrite newer configuration. Refused requests can start a fresh action; unresolved/tombstoned outcomes allow only explicit original-request replay, never a replacement action.
Why: Queue acceptance cannot prove a setting changed, and a reused inbound id cannot authorize changing another destination. No automatic settings replay and no reply draft mutation. Undo: remove the control while preserving pending request storage. By: agent, within Ivan's native parity audit.


## 2026-10-18 · Archive state follows the observed destination

An owner hide event retains the message identity observed at its journal position. When a trusted replacement changes source, contact or target for the same id, discard its prior local hidden membership. Same-identity updates remain archived; replay derives the same result without writing an unhide event. This fixes historical archive leakage without guessing identity for a late legacy id-only hide. Send and Archive remains a separate receipt-bound collector contract.

## 2026-10-18 · Remembered receipt-bound Send and Archive

The native send menu remembers the primary action per Hub. Archive intent and the exact open conversation members are persisted with the original send request before transport. Only a matching collector archive receipt applies, with original version and provider receipt required for guarded Teams. Recheck each member's current target/contact, preserve newer drafts, and never include arrivals after submission. Custom scheduling explicitly omits archive intent. Missing capabilities or oversized selections explain the refusal without sending a partial selection. Plain-provider duplicate confirmation uses the collector's successful command outcome, matching ordinary send confirmation; it does not invent a provider receipt.

The original request token remains authoritative after reload even when a refreshed message lacks its editor token. Another pending reply is excluded from a grouped archive both at selection and at confirmation. Native folder semantics remain: the delivered reply is in Sent; older archived members without a reply are in Archive. Restore remains available, and replayed archive success cannot undo it.
### 2026-10-18 — Provider-local contact identities

Decided: Use the same source-family/contact tuple for list grouping, selected detail,
pins, unread state and archive membership. Telegram and WhatsApp may reuse a contact
identifier without sharing a thread. Teams DM, channel and mention retain one family.
Why: a hostile review found that raw-contact grouping combined unrelated histories
while archive and pins already used the provider boundary. Keep the existing serialized
pin/read keys, with no migration or loss of drafts. Undo: revert the grouping alias;
stored preferences remain compatible. By: agent.


### 2026-10-18 — Native conversation context and action glyphs
Use the provider plus its distinct place once, matching pinned native Letter.origin. Do not synthesize a second Teams category before the supplied place. Deduplicate identical source context across conversation members. All action-row icons use22px in the labelled layout and28px in the existing compact layout; the shared React SVG previously inherited16px. Keep44px targets and existing reaction/draft semantics. Bounded native alignment, not a new layout.


### 2026-10-18 — Native Inbox list state and display names
Display native-style draft, suggested reaction and delivery marks beside each conversation name. Unconfirmed delivery stays distinct from Sent; pending or failed work remains visible alongside a retained draft, and a successful retry supersedes its old failure. Suggested emoji is content, never a delivered reaction. Strip only bracketed UTC/GMT hour metadata from rendered person names, retaining the original value for provider identity, requests and persisted drafts. Reuse existing native icon assets and the shared edit icon.


### 2026-10-18 — Native Inbox folder affordance
Reuse the pinned native tray asset beside Inbox and let this control occupy the remaining folder space. Put Sort before Compose, matching native reading order. Keep web-only Inbox options reachable; do not remove functional controls for a screenshot match. When Failed appears, keep Inbox accessible by its label and compact its visible text so every target still fits the pane. Remaining toolbar surfaces and extra options placement need a separate native comparison.
