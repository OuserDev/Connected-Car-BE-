// tabs/store.js
import { Api } from '../api.js';
import { UI } from '../ui/components.js';
import { getRoot } from '../core/shared.js';

export function renderStore() {
    const root = getRoot();
    root.innerHTML = `
    <div class="stack">

      <div class="card"><div class="body">
        <div class="store-section" id="secNew">
          <div class="hdr"><div class="ttl">새 상품</div></div>
          <div class="product-grid" id="newGrid"></div>
        </div>
      </div></div>

      <div class="card"><div class="body">
        <div class="store-section" id="secUsed">
          <div class="used-head">
            <div class="ttl">중고 장터</div>
            <button class="btn" id="btnWrite">판매글 작성</button>
          </div>
          <div class="used-list" id="usedList"></div>
        </div>
      </div></div>

      <div class="card"><div class="body">
        <div class="store-section" id="secPay">
          <div class="hdr">
            <div class="ttl">결제 수단</div>
            <div style="display:flex; gap:8px">
              <!-- 변경: 테스트 카드 → 카드 추가 -->
              <button class="btn ghost" id="btnAddCard">+ 카드 추가</button>
            </div>
          </div>
          <div class="pay-cards" id="cardsWrap"></div>
          <div class="muted" style="margin-top:6px">
            실제 카드번호는 보안상 마스킹됩니다. (모의/테스트 카드만 전체 표시 허용)
          </div>
        </div>
      </div></div>

    </div>

    <dialog class="modal" id="dlgUsed">
      <div class="hd">판매글 작성</div>
      <form method="dialog" id="usedForm">
        <div class="bd">
          <div class="form-row">
            <label>제목</label>
            <input type="text" id="fTitle" placeholder="예: 순정 가죽 핸들커버" required />
          </div>
          <div class="form-row"><label>내용</label>
            <textarea id="fBody" placeholder="상품 설명을 입력하세요."></textarea>
          </div>
          <div class="form-row"><label>금액(원)</label>
            <input type="number" id="fPrice" inputmode="numeric" min="0" step="1" placeholder="예: 15000" required />
          </div>
        </div>
        <div class="ft">
          <button class="btn ghost" type="button" id="btnCancel">취소</button>
          <button class="btn brand" id="btnSubmit">작성하기</button>
        </div>
      </form>
    </dialog>

    <!-- 신규: 카드 추가 모달 -->
    <dialog class="modal" id="dlgCard">
      <div class="hd">카드 추가</div>
      <form method="dialog" id="cardForm">
        <div class="bd">
          <div class="form-row">
            <label>카드 번호</label>
            <input type="text" id="cNumber" inputmode="numeric" placeholder="1234 5678 1234 5678" maxlength="23" required />
          </div>
          <div class="form-row">
            <label>이름(영문)</label>
            <input type="text" id="cHolder" placeholder="HONG GILDONG" required />
          </div>
          <div class="form-row">
            <label>유효기간 (MM/YY)</label>
            <input type="text" id="cExp" inputmode="numeric" placeholder="08/27" maxlength="5" required />
          </div>
          <div class="form-row">
            <label>CVC</label>
            <input type="password" id="cCvc" inputmode="numeric" placeholder="3자리" maxlength="4" />
            <div class="muted">보안상 저장하지 않습니다.</div>
          </div>
          <div class="form-row">
            <label class="chk" style="display:flex; gap:8px; align-items:center;">
              <input type="checkbox" id="cDefault" />
              <span>추가 후 기본 결제수단으로 설정</span>
            </label>
          </div>
        </div>
        <div class="ft">
          <button class="btn ghost" type="button" id="btnCardCancel">취소</button>
          <button class="btn brand" id="btnCardSubmit" type="submit">추가</button>
        </div>
      </form>
    </dialog>

    <!-- 신규: 게시글 상세보기 모달 -->
    <dialog class="modal wide" id="dlgPostDetail">
      <div class="hd">
        <span id="detailTitle">게시글 상세</span>
        <button class="btn-close" id="btnDetailClose">×</button>
      </div>
      <div class="bd" style="max-height: 70vh; overflow-y: auto;">
        <div id="detailContent">
          <!-- 상세 내용이 여기에 로드됩니다 -->
        </div>
      </div>
      <div class="ft" id="detailActions">
        <!-- 작성자인 경우 수정/삭제 버튼, 아닌 경우 연락하기 등 -->
      </div>
    </dialog>
  `;

    const $newGrid = document.getElementById('newGrid');
    const $usedList = document.getElementById('usedList');
    const $cardsWrap = document.getElementById('cardsWrap');
    const $btnWrite = document.getElementById('btnWrite');
    const $dlg = document.getElementById('dlgUsed');
    const $form = document.getElementById('usedForm');
    const $btnSubmit = document.getElementById('btnSubmit');
    const $btnCancel = document.getElementById('btnCancel');

    // 신규: 카드 추가 요소들
    const $dlgCard = document.getElementById('dlgCard');
    const $cardForm = document.getElementById('cardForm');
    const $btnAddCard = document.getElementById('btnAddCard');
    const $btnCardCancel = document.getElementById('btnCardCancel');
    const $btnCardSubmit = document.getElementById('btnCardSubmit');
    const $cNumber = document.getElementById('cNumber');
    const $cHolder = document.getElementById('cHolder');
    const $cExp = document.getElementById('cExp');
    const $cCvc = document.getElementById('cCvc');
    const $cDefault = document.getElementById('cDefault');

    const $fTitle = document.getElementById('fTitle');
    const $fBody = document.getElementById('fBody');
    const $fPrice = document.getElementById('fPrice');

    const fmtWon = (n) => (n || 0).toLocaleString() + '원';

    function renderNew(items) {
        $newGrid.innerHTML = '';
        items.forEach((it) => {
            const el = document.createElement('div');
            el.className = 'product-card';
            el.innerHTML = `
        <div class="thumb">${it.img || '🛠️'}</div>
        <div class="name">${it.title}</div>
        <div class="desc">${it.desc || ''}</div>
        <div class="foot">
          <div class="price">${fmtWon(it.price)}</div>
          <button class="btn" data-id="${it.id}">구매</button>
        </div>`;
            el.querySelector('button').addEventListener('click', async (e) => {
                e.preventDefault();
                UI.toast('구매 기능은 추후 구현 예정입니다');
            });
            $newGrid.appendChild(el);
        });
    }

    function renderUsed(items) {
        $usedList.innerHTML = '';
        if (!items.length) {
            $usedList.innerHTML = `<div class="muted">등록된 판매글이 없습니다. 첫 글을 작성해보세요.</div>`;
            return;
        }
        items.forEach((it) => {
            const el = document.createElement('div');
            el.className = 'used-item';
            el.style.cursor = 'pointer'; // 클릭 가능하도록

            // 상태별 표시
            const statusBadge = it.status === 'sold' ? '<span class="tag sold">판매완료</span>' : it.status === 'reserved' ? '<span class="tag reserved">예약중</span>' : '';

            el.innerHTML = `
        <div class="ph">🖼️</div>
        <div class="meta">
          <div class="t">${it.title} ${statusBadge}</div>
          <div class="p">${fmtWon(it.price)} · <span class="muted">판매자: ${it.seller}</span></div>
          <div class="p2"><span class="muted">조회 ${it.view_count || 0} · ${new Date(it.created_at).toLocaleString()}</span></div>
          <div class="d">${(it.body || '').slice(0, 120)}</div>
        </div>`;

            // 게시글 클릭 시 상세보기
            el.addEventListener('click', async () => {
                try {
                    const res = await Api.getMarketPost(it.id);
                    if (!res.ok) {
                        UI.toast(res.message || '상세 조회 실패');
                        return;
                    }
                    const post = res.post;
                    // 상세 모달 내용 구성
                    document.getElementById('detailTitle').textContent = post.title;
                    document.getElementById('detailContent').innerHTML = `
                        <div style="font-size:1.2em; font-weight:bold; margin-bottom:8px;">${post.title}</div>
                        <div class="muted" style="margin-bottom:8px;">${post.seller} · ${new Date(post.created_at).toLocaleString()} · 조회 ${post.view_count}</div>
                        <div style="margin-bottom:12px; color:#444; white-space:pre-line;">${post.body}</div>
                        <div style="font-weight:bold; font-size:1.1em; color:#1976d2; margin-bottom:8px;">${fmtWon(post.price)}</div>
                        <div style="margin-bottom:8px;">상태: <span class="tag ${post.status}">${post.status === 'sold' ? '판매완료' : post.status === 'reserved' ? '예약중' : '판매중'}</span></div>
                    `;
                    // 작성자 여부에 따라 버튼 표시
                    const $actions = document.getElementById('detailActions');
                    $actions.innerHTML = '';
                    if (post.is_author) {
                        $actions.innerHTML = `
                            <button class="btn" id="btnEditPost">수정</button>
                            <button class="btn ghost" id="btnDeletePost">삭제</button>
                        `;
                        
                        // 수정 버튼 이벤트
                        document.getElementById('btnEditPost').addEventListener('click', () => {
                            // 기존 작성 폼에 데이터 채우기
                            $fTitle.value = post.title;
                            $fBody.value = post.body;
                            $fPrice.value = post.price;
                            
                            // 수정 모드임을 표시
                            $dlg.querySelector('.hd').textContent = '판매글 수정';
                            $btnSubmit.textContent = '수정하기';
                            $btnSubmit.dataset.editId = post.id;
                            
                            $dlgPostDetail.close();
                            $dlg.showModal();
                        });
                        
                        // 삭제 버튼 이벤트
                        document.getElementById('btnDeletePost').addEventListener('click', async () => {
                            if (!confirm('정말 삭제하시겠습니까?')) return;
                            
                            const res = await Api.deleteMarketPost(post.id);
                            if (res.ok) {
                                UI.toast(res.message || '게시글이 삭제되었습니다.');
                                $dlgPostDetail.close();
                                // 목록 새로고침
                                const u = await Api.getMarketPosts();
                                if (u.ok) renderUsed(u.posts);
                            } else {
                                UI.toast(res.message || '삭제 실패');
                            }
                        });
                    } else {
                        $actions.innerHTML = `<button class="btn" id="btnContact">연락하기</button>`;
                        
                        // 연락하기 버튼 이벤트
                        document.getElementById('btnContact').addEventListener('click', () => {
                            UI.toast('연락하기 기능은 추후 구현 예정입니다.');
                        });
                    }
                    document.getElementById('dlgPostDetail').showModal();
                } catch (e) {
                    UI.toast('상세 조회 중 오류 발생');
                }
            });

            $usedList.appendChild(el);
        });
    }

    const mask = (_, last4) => `**** **** **** ${last4}`;
    function renderCards(cards, activeId) {
        $cardsWrap.innerHTML = '';
        cards.forEach((c) => {
            const row = document.createElement('label');
            row.className = 'card-item';
            // 카드사명 매핑 (Unknown → 실제 카드사명)
            const cardBrandName = {
                'VISA': 'VISA',
                'Mastercard': 'Mastercard', 
                'Unknown': '현대카드',  // Unknown일 때 현대카드로 표시
                'AMEX': 'American Express',
                'Discover': 'Discover'
            }[c.brand] || c.brand;
            
            row.innerHTML = `
        <input type="radio" name="paycard" value="${c.id}" ${c.id === activeId ? 'checked' : ''} />
        <div>
          <div class="brand">${cardBrandName}</div>
          <div class="num" ${c.isTest && c.fullNumber ? `data-full="${c.fullNumber}"` : ''}>${mask('', c.last4)}</div>
          <div class="sub">만료 ${c.exp} · ${c.holder}${c.isTest ? ' · 테스트 카드' : ''}</div>
          <div class="row" style="margin-top:6px; gap:8px;">
            ${c.isTest && c.fullNumber ? '<button class="link-btn btnShowFull" type="button">테스트 번호 보기</button>' : ''}
            ${c.id !== activeId ? '<button class="link-btn btnSetDefault" type="button">기본으로 설정</button>' : '<span class="tag">기본</span>'}
          </div>
        </div>`;
            // 라디오 변경시 기본 설정
            row.querySelector('input').addEventListener('change', async () => {
                await Api.cardSelect(c.id);
                UI.toast(`결제카드 선택: ****${c.last4}`);
            });
            // 전체 보기(테스트 카드 전용)
            const btnShow = row.querySelector('.btnShowFull');
            if (btnShow) {
                btnShow.addEventListener('click', () => {
                    const numEl = row.querySelector('.num');
                    const full = numEl.getAttribute('data-full');
                    if (full) {
                        numEl.textContent = full;
                        btnShow.remove();
                    }
                });
            }
            // 기본으로 설정 버튼
            const btnDef = row.querySelector('.btnSetDefault');
            if (btnDef) {
                btnDef.addEventListener('click', async () => {
                    const r = await Api.cardSelect(c.id);
                    if (r?.ok) {
                        UI.toast(`기본 결제수단 설정: ****${c.last4}`);
                        loadCards();
                    } else {
                        UI.toast(r?.message || '기본 설정 실패');
                    }
                });
            }
            $cardsWrap.appendChild(row);
        });
    }

    async function loadAll() {
        const [n, u] = await Promise.all([Api.storeNew(), Api.getMarketPosts()]);
        if (n.ok) renderNew(n.items);
        if (u.ok) renderUsed(u.posts); // posts 필드로 변경
        await loadCards();
    }

    async function loadCards() {
        const c = await Api.cardsList();
        if (c.ok) renderCards(c.cards, c.activeId);
    }

    // ---------- 카드 입력 유틸 & 검증 ----------
    const onlyDigits = (s) => (s || '').replace(/\D+/g, '');
    const formatCard = (digits) => {
        // 4자리씩 띄어쓰기 (Amex 4-6-5도 고려 가능하지만 단순 4단위로 표기)
        return digits
            .replace(/\D/g, '')
            .replace(/(.{4})/g, '$1 ')
            .trim();
    };
    const detectBrand = (digits) => {
        if (/^4\d{12,18}$/.test(digits)) return 'VISA';
        if (/^5[1-5]\d{14}$/.test(digits)) return 'Mastercard';
        if (/^(34|37)\d{13}$/.test(digits)) return 'AMEX';
        if (/^6(011|5)\d{14,16}$/.test(digits)) return 'Discover';
        return 'CARD';
    };
    // Luhn 체크
    const luhnCheck = (digits) => {
        let sum = 0,
            alt = false;
        for (let i = digits.length - 1; i >= 0; i--) {
            let n = parseInt(digits[i], 10);
            if (alt) {
                n *= 2;
                if (n > 9) n -= 9;
            }
            sum += n;
            alt = !alt;
        }
        return sum % 10 === 0;
    };
    const parseExp = (val) => {
        const m = (val || '').replace(/\s/g, '').match(/^(\d{1,2})\/?(\d{2})$/);
        if (!m) return null;
        let mm = parseInt(m[1], 10);
        let yy = parseInt(m[2], 10);
        return { mm, yy };
    };
    const isValidMonth = (mm) => mm >= 1 && mm <= 12;
    const isFutureExp = ({ mm, yy }) => {
        // YY → 2000~2099로 해석
        const fullY = 2000 + yy;
        const now = new Date();
        const y = now.getFullYear(),
            m = now.getMonth() + 1;
        return fullY > y || (fullY === y && mm >= m);
    };

    // 포맷팅 UX
    $cNumber.addEventListener('input', () => {
        const digits = onlyDigits($cNumber.value).slice(0, 19); // 19자리까지 허용
        $cNumber.value = formatCard(digits);
    });
    $cExp.addEventListener('input', () => {
        let v = $cExp.value.replace(/[^\d]/g, '').slice(0, 4);
        if (v.length >= 3) v = v.slice(0, 2) + '/' + v.slice(2);
        $cExp.value = v;
    });

    // ---------- 모달/폼: 중고 판매글 ----------
    document.getElementById('btnWrite').addEventListener('click', () => {
        // 새 작성 모드로 초기화
        $dlg.querySelector('.hd').textContent = '판매글 작성';
        $btnSubmit.textContent = '작성하기';
        delete $btnSubmit.dataset.editId;
        $dlg.showModal();
    });
    $btnCancel.addEventListener('click', () => {
        $dlg.close();
        $form.reset();
        delete $btnSubmit.dataset.editId;
    });
    $dlg.addEventListener('close', () => {
        $form.reset();
        delete $btnSubmit.dataset.editId;
    });
    $form.addEventListener('submit', async (e) => {
        e.preventDefault();
        $btnSubmit.disabled = true;
        try {
            const payload = {
                title: $fTitle.value.trim(),
                body: $fBody.value.trim(),
                price: Number($fPrice.value || 0),
            };
            
            let r;
            const editId = $btnSubmit.dataset.editId;
            
            if (editId) {
                // 수정 모드
                r = await Api.updateMarketPost(editId, payload);
            } else {
                // 작성 모드
                r = await Api.createMarketPost(payload);
            }
            
            if (!r.ok) {
                UI.toast(r.message || (editId ? '수정 실패' : '작성 실패'));
                return;
            }
            UI.toast(r.message || (editId ? '게시글이 수정되었습니다.' : '판매글이 등록되었습니다.'));
            $dlg.close();
            const u = await Api.getMarketPosts();
            if (u.ok) renderUsed(u.posts);
        } finally {
            $btnSubmit.disabled = false;
        }
    });

    // ---------- 모달/폼: 상세보기 ----------
    const $dlgPostDetail = document.getElementById('dlgPostDetail');
    const $btnDetailClose = document.getElementById('btnDetailClose');
    
    $btnDetailClose.addEventListener('click', () => {
        $dlgPostDetail.close();
    });

    // ---------- 모달/폼: 카드 추가 ----------
    $btnAddCard.addEventListener('click', () => {
        $cardForm.reset();
        $dlgCard.showModal();
    });
    $btnCardCancel.addEventListener('click', () => {
        $dlgCard.close();
        $cardForm.reset();
    });
    $dlgCard.addEventListener('close', () => {
        $cardForm.reset();
    });

    $cardForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        $btnCardSubmit.disabled = true;
        try {
            // 1) 입력 정규화
            const numberDigits = onlyDigits($cNumber.value);
            const holder = ($cHolder.value || '').trim().replace(/\s+/g, ' ');
            const expParsed = parseExp($cExp.value);
            const cvc = onlyDigits($cCvc.value);
            const setDefault = !!$cDefault.checked;

            // 2) 엄격 검증 (최소 7가지)
            // (a) 길이 13~19
            if (numberDigits.length < 13 || numberDigits.length > 19) {
                UI.toast('카드번호가 올바르지 않습니다. (13~19자리)');
                return;
            }
            // (b) Luhn
            if (!luhnCheck(numberDigits)) {
                UI.toast('유효하지 않은 카드번호(Luhn)입니다.');
                return;
            }
            // (c) 이름
            if (holder.length < 2) {
                UI.toast('이름을 정확히 입력해주세요.');
                return;
            }
            // (d) 유효기간 파싱/형식
            if (!expParsed) {
                UI.toast('유효기간 형식이 올바르지 않습니다. (MM/YY)');
                return;
            }
            // (e) 월 범위
            if (!isValidMonth(expParsed.mm)) {
                UI.toast('유효기간의 월(MM)이 올바르지 않습니다.');
                return;
            }
            // (f) 미래/현재 유효
            if (!isFutureExp(expParsed)) {
                UI.toast('이미 만료된 카드입니다.');
                return;
            }
            // (g) CVC 길이(선제 검증만, 저장 금지)
            if (cvc && (cvc.length < 3 || cvc.length > 4)) {
                UI.toast('CVC는 3~4자리입니다.');
                return;
            }

            const brand = detectBrand(numberDigits);
            const last4 = numberDigits.slice(-4);
            const expStr = `${String(expParsed.mm).padStart(2, '0')}/${String(expParsed.yy).padStart(2, '0')}`;

            // 중복 체크: 동일 last4 + exp + holder 존재 시 경고
            const current = await Api.cardsList();
            if (current?.ok && current.cards?.some((x) => x.last4 === last4 && x.exp === expStr && x.holder === holder)) {
                UI.toast('동일한 카드가 이미 등록되어 있습니다.');
                return;
            }

            // 전송 페이로드 (주의: prod에선 토큰화/PG 전송 후 토큰만 저장)
            const payload = {
                brand,
                holder,
                exp: expStr,
                last4,
                // 보안: fullNumber/CVC는 백엔드로 전송 후 절대 저장하지 말 것 (모의환경만)
                fullNumber: numberDigits,
                cvc,
                isTest: false,
                setDefault,
            };

            const r = await Api.cardsAdd(payload);
            if (!r?.ok) {
                UI.toast(r?.message || '카드 추가 실패');
                return;
            }

            UI.toast('카드가 추가되었습니다.');

            // 리스트 갱신
            await loadCards();

            // 사용자가 기본설정 체크했는데 백엔드가 처리 안 해줬을 경우 대비:
            if (setDefault) {
                const after = await Api.cardsList();
                if (after?.ok) {
                    const found = after.cards.find((x) => x.last4 === last4 && x.exp === expStr && x.holder === holder);
                    if (found && after.activeId !== found.id) {
                        const sel = await Api.cardSelect(found.id);
                        if (sel?.ok) {
                            UI.toast(`기본 결제수단 설정: ****${last4}`);
                            await loadCards();
                        }
                    }
                }
            }

            // 민감정보 즉시 파기 (프론트 메모리/DOM)
            $cNumber.value = '';
            $cCvc.value = '';
            $dlgCard.close();
        } finally {
            $btnCardSubmit.disabled = false;
        }
    });

    loadAll();
}
