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
