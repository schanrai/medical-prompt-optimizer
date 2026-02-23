/**
 * Medical Question Framing Tool - Client-Side UI Logic
 *
 * Handles:
 * - Real-time word counting with visual feedback
 * - Form submission to POST /api/check
 * - Dynamic rendering of display_blocks from API response
 * - Clickable clarification options that populate input field
 * - "Ask Another Question" button to reset UI state
 * - Error handling and validation feedback
 *
 * Design system: see /static/design-system.md
 * Tailwind tokens are defined in the <script> config block in index.html.
 * Class strings here must match those tokens — update design-system.md if changed.
 */

// ============================================================================
// DOM Elements
// ============================================================================

const form = document.getElementById('question-form');
const textarea = document.getElementById('question-input');
const submitBtn = document.getElementById('submit-btn');
const wordCountDisplay = document.getElementById('word-count');
const wordWarning = document.getElementById('word-warning');
const validationError = document.getElementById('validation-error');
const resultArea = document.getElementById('result-area');

// ============================================================================
// Word Counter
// ============================================================================

/**
 * Count words in text (matches backend logic in validation.py)
 * Splits on whitespace, filters empty strings
 */
function countWords(text) {
    if (!text || text.trim() === '') return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Update word counter display and show warning if approaching or exceeding limit
 */
function updateWordCounter() {
    const text = textarea.value;
    const wordCount = countWords(text);

    wordCountDisplay.textContent = wordCount;

    if (wordCount > 500) {
        wordWarning.textContent = '⚠ Exceeds limit (500 words max)';
        wordWarning.classList.remove('hidden', 'text-clarify-900');
        wordWarning.classList.add('text-danger-900');
    } else if (wordCount >= 450) {
        wordWarning.textContent = '⚠ Approaching limit (500 words)';
        wordWarning.classList.remove('hidden', 'text-danger-900');
        wordWarning.classList.add('text-clarify-900');
    } else {
        wordWarning.classList.add('hidden');
    }
}

textarea.addEventListener('input', updateWordCounter);

// ============================================================================
// Form Submission
// ============================================================================

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    hideValidationError();
    hideResultArea();

    const question = textarea.value.trim();

    if (!question) {
        showValidationError('Please enter a question.');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Analyzing...
    `;

    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            renderResult(data.data);
        } else {
            const errorMessage = data.error || 'An unexpected error occurred. Please try again.';
            showValidationError(errorMessage);
        }
    } catch (error) {
        console.error('Request failed:', error);
        showValidationError('Unable to connect to the server. Please check your connection and try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check Question';
    }
});

// ============================================================================
// Error Display
// ============================================================================

function showValidationError(message) {
    validationError.querySelector('p').textContent = message;
    validationError.classList.remove('hidden');
}

function hideValidationError() {
    validationError.classList.add('hidden');
    validationError.querySelector('p').textContent = '';
}

// ============================================================================
// Result Rendering
// ============================================================================

/**
 * Render API response data
 * @param {Object} data - API response containing display_blocks array
 */
function renderResult(data) {
    if (!data || !data.display_blocks || data.display_blocks.length === 0) {
        showValidationError('Received an empty response from the server.');
        return;
    }

    resultArea.innerHTML = '';

    data.display_blocks.forEach(block => {
        const blockElement = createDisplayBlock(block);
        if (blockElement) {
            resultArea.appendChild(blockElement);
        }
    });

    resultArea.appendChild(createAskAnotherButton());
    resultArea.classList.remove('hidden');
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Route a display block to its renderer by type
 * @param {Object} block - Display block with type, subtype, and content
 * @returns {HTMLElement|null}
 */
function createDisplayBlock(block) {
    const { type, content } = block;

    switch (type) {
        case 'emergency_warning':
        case 'crisis_warning':
            return createCrisisWarning(content);
        case 'main_content':
            return createMainContent(content, block.subtype);
        case 'healthcare_reminder':
            return createHealthcareReminder(content);
        case 'footer':
            return createFooterBlock(content);
        default:
            console.warn('Unknown block type:', type);
            return null;
    }
}

// ============================================================================
// Block Renderers
// ============================================================================

/**
 * Crisis warning banner — danger token set, left-border accent
 * Used for: self-harm (988), drug-seeking (SAMHSA), physical emergency (911)
 */
function createCrisisWarning(content) {
    const div = document.createElement('div');
    div.className = 'bg-danger-50 border-l-4 border-danger-500 p-4 rounded-r-xl';
    div.innerHTML = `
        <div class="flex items-start gap-3">
            <svg class="h-5 w-5 text-danger-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            <p class="text-sm font-medium text-danger-900">${escapeHtml(content)}</p>
        </div>
    `;
    return div;
}

/**
 * Main content block — varies by response subtype
 */
function createMainContent(content, subtype) {
    const div = document.createElement('div');

    if (subtype === 'clarification') {
        // CLARIFICATION: reasoning + numbered clickable rewrite options
        div.className = 'bg-white border border-warm-100 rounded-2xl p-6';
        div.innerHTML = `
            <h2 class="text-xl font-bold text-clarify-900 mb-2">Your question needs clarification</h2>
            <p class="text-sm text-warm-600 mb-5">${escapeHtml(content.reasoning)}</p>
            <p class="text-xs font-medium text-warm-700 uppercase tracking-widest mb-3">Suggested rewrites — click to use</p>
            <div class="space-y-2">
                ${content.clarification_options.map((option, index) => `
                    <div
                        class="clarification-option group relative w-full text-left px-4 py-3 bg-white hover:bg-warm-50 border border-warm-100 rounded-xl transition-colors duration-150 cursor-pointer flex items-start gap-3"
                        data-rewrite="${escapeHtml(option.rewritten_question)}"
                        role="button"
                        tabindex="0"
                    >
                        <span class="flex-shrink-0 w-7 h-7 rounded-full bg-warm-100 flex items-center justify-center text-xs font-semibold text-warm-700 mt-0.5">${index + 1}</span>
                        <div class="flex-1 min-w-0 pr-8">
                            <div class="text-sm font-semibold text-warm-900 mb-0.5">${escapeHtml(option.label)}</div>
                            <div class="text-sm text-warm-600">${escapeHtml(option.rewritten_question)}</div>
                        </div>
                        <button
                            class="copy-btn absolute top-3 right-3 p-1.5 rounded-lg text-warm-400 hover:text-warm-700 hover:bg-warm-100 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-warm-900"
                            data-copy="${escapeHtml(option.rewritten_question)}"
                            title="Copy to clipboard"
                            aria-label="Copy to clipboard"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;

        div.querySelectorAll('.clarification-option').forEach(optionDiv => {
            optionDiv.addEventListener('click', (e) => {
                if (e.target.closest('.copy-btn')) return;
                populateInputWithRewrite(optionDiv.getAttribute('data-rewrite'));
            });
            optionDiv.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    populateInputWithRewrite(optionDiv.getAttribute('data-rewrite'));
                }
            });
        });

        div.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const text = btn.getAttribute('data-copy');
                try {
                    await navigator.clipboard.writeText(text);
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
                    btn.classList.add('text-green-600');
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                        btn.classList.remove('text-green-600');
                    }, 1500);
                } catch (err) {
                    console.error('Failed to copy to clipboard:', err);
                }
            });
        });

    } else if (subtype === 'confirmation') {
        // CONFIRMATION: success card with checkmark icon
        div.className = 'bg-success-50 border border-success-500 rounded-2xl p-6';
        div.innerHTML = `
            <div class="flex items-start gap-4 mb-5">
                <div class="flex-shrink-0 w-10 h-10 bg-success-500 rounded-full flex items-center justify-center">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <div class="pt-1">
                    <h2 class="text-xl font-bold text-success-900 mb-1">Your question is well-structured</h2>
                    <p class="text-sm text-success-900">Clear and specific enough for research purposes.</p>
                </div>
            </div>
            <div class="bg-white border border-warm-100 rounded-xl p-4">
                <p class="text-xs font-medium text-warm-700 uppercase tracking-widest mb-2">Confirmed Prompt</p>
                <p class="text-sm text-warm-900 leading-relaxed">"${escapeHtml(content)}"</p>
            </div>
        `;

    } else if (subtype === 'out_of_scope') {
        // OUT_OF_SCOPE: danger card with X icon
        div.className = 'bg-danger-50 border border-danger-500 rounded-2xl p-6';
        div.innerHTML = `
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-10 h-10 bg-danger-500 rounded-full flex items-center justify-center">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </div>
                <div class="pt-1">
                    <h2 class="text-xl font-bold text-danger-900 mb-2">Out of scope</h2>
                    <p class="text-sm text-danger-900 leading-relaxed">${escapeHtml(content)}</p>
                </div>
            </div>
        `;

    } else {
        // Fallback for unexpected content
        div.className = 'bg-white border border-warm-100 rounded-2xl p-6';
        div.innerHTML = `<p class="text-sm text-warm-600">${escapeHtml(typeof content === 'string' ? content : JSON.stringify(content))}</p>`;
    }

    return div;
}

/**
 * Healthcare reminder banner — info token set, left-border accent
 */
function createHealthcareReminder(content) {
    const div = document.createElement('div');
    div.className = 'bg-info-50 border-l-4 border-info-500 p-4 rounded-r-xl';
    div.innerHTML = `
        <div class="flex items-start gap-3">
            <svg class="h-5 w-5 text-info-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
            <p class="text-sm text-info-900">${escapeHtml(content)}</p>
        </div>
    `;
    return div;
}

/**
 * Footer block — plain closing copy, no border or background.
 * Intentionally low visual weight; just a quiet nudge, not an alert.
 */
function createFooterBlock(content) {
    const div = document.createElement('div');
    div.className = 'pt-1';
    div.innerHTML = `<p class="text-sm text-warm-600">${escapeHtml(content)}</p>`;
    return div;
}

/**
 * "Ask Another Question" — plain text link, no button chrome.
 * Secondary action only; should not compete visually with the primary CTA.
 */
function createAskAnotherButton() {
    const wrapper = document.createElement('div');
    wrapper.className = 'mt-5 text-center';

    const link = document.createElement('button');
    link.type = 'button';
    link.className = 'text-sm text-warm-700 underline underline-offset-2 hover:text-warm-900 transition-colors duration-150 focus:outline-none';
    link.textContent = 'Ask another question';
    link.addEventListener('click', resetUI);

    wrapper.appendChild(link);
    return wrapper;
}

// ============================================================================
// UI State Management
// ============================================================================

/**
 * Populate input with a clarification rewrite and scroll back to form
 */
function populateInputWithRewrite(rewrite) {
    textarea.value = rewrite;
    updateWordCounter();
    hideResultArea();
    textarea.focus();
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Reset UI to initial empty state
 */
function resetUI() {
    textarea.value = '';
    updateWordCounter();
    hideResultArea();
    hideValidationError();
    textarea.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function hideResultArea() {
    resultArea.classList.add('hidden');
    resultArea.innerHTML = '';
}

// ============================================================================
// Utilities
// ============================================================================

/**
 * Escape HTML to prevent XSS
 * Belt-and-suspenders: backend also sanitizes, but client-side defence is good practice
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Initialization
// ============================================================================

updateWordCounter();
