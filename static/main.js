/**
 * Medical Research Prompt Optimizer - Client-Side UI Logic
 * 
 * Handles:
 * - Real-time word counting with visual feedback
 * - Form submission to POST /api/check
 * - Dynamic rendering of display_blocks from API response
 * - Clickable clarification options that populate input field
 * - "Ask Another Question" button to reset UI state
 * - Error handling and validation feedback
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
    
    // Show appropriate warning based on word count
    if (wordCount > 500) {
        wordWarning.textContent = '⚠️ Exceeds limit (500 words max)';
        wordWarning.classList.remove('hidden');
        wordWarning.classList.remove('text-amber-600');
        wordWarning.classList.add('text-red-600');
    } else if (wordCount >= 450) {
        wordWarning.textContent = '⚠️ Approaching limit (500 words)';
        wordWarning.classList.remove('hidden');
        wordWarning.classList.remove('text-red-600');
        wordWarning.classList.add('text-amber-600');
    } else {
        wordWarning.classList.add('hidden');
    }
}

// Attach word counter to textarea input
textarea.addEventListener('input', updateWordCounter);

// ============================================================================
// Form Submission
// ============================================================================

/**
 * Handle form submission
 * - Prevent default browser behavior
 * - Clear previous results/errors
 * - Submit to POST /api/check
 * - Render response or show error
 */
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    // Clear previous state
    hideValidationError();
    hideResultArea();
    
    const question = textarea.value.trim();
    
    // Client-side check (belt-and-suspenders, backend validates too)
    if (!question) {
        showValidationError('Please enter a question.');
        return;
    }
    
    // Show loading state with spinner
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Analyzing...
    `;
    
    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Success: render display_blocks
            renderResult(data.data);
        } else {
            // API returned error (validation rejection or other error)
            const errorMessage = data.error || 'An unexpected error occurred. Please try again.';
            showValidationError(errorMessage);
        }
    } catch (error) {
        // Network error or JSON parse error
        console.error('Request failed:', error);
        showValidationError('Unable to connect to the server. Please check your connection and try again.');
    } finally {
        // Re-enable submit button
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
 * @param {Object} data - API response data containing display_blocks array
 */
function renderResult(data) {
    if (!data || !data.display_blocks || data.display_blocks.length === 0) {
        showValidationError('Received an empty response from the server.');
        return;
    }
    
    // Clear previous result
    resultArea.innerHTML = '';
    
    // Render each display block in order
    data.display_blocks.forEach(block => {
        const blockElement = createDisplayBlock(block);
        if (blockElement) {
            resultArea.appendChild(blockElement);
        }
    });
    
    // Add "Ask Another Question" button at the end
    const askAnotherBtn = createAskAnotherButton();
    resultArea.appendChild(askAnotherBtn);
    
    // Show result area
    resultArea.classList.remove('hidden');
    
    // Scroll to results
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Create a display block element based on block type
 * @param {Object} block - Display block with type and content
 * @returns {HTMLElement|null}
 */
function createDisplayBlock(block) {
    const { type, content } = block;
    
    switch (type) {
        case 'emergency_warning':
            return createEmergencyWarning(content);
        
        case 'main_content':
            return createMainContent(content, block.subtype);
        
        case 'healthcare_reminder':
            return createHealthcareReminder(content);
        
        case 'footer':
            return createClosingMessage(content);
        
        default:
            console.warn('Unknown block type:', type);
            return null;
    }
}

/**
 * Create emergency warning block (red alert box)
 */
function createEmergencyWarning(content) {
    const div = document.createElement('div');
    div.className = 'bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg mb-4';
    div.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium text-red-800">${escapeHtml(content)}</p>
            </div>
        </div>
    `;
    return div;
}

/**
 * Create main content block (varies by response type)
 */
function createMainContent(content, subtype) {
    const div = document.createElement('div');
    
    if (subtype === 'clarification') {
        // CLARIFICATION response type
        div.className = 'bg-white border border-gray-200 rounded-lg p-6 mb-4';
        
        // Format reasoning as bullet points for better readability
        const reasoningSentences = content.reasoning.split(/\.\s+/).filter(s => s.trim().length > 0);
        const reasoningHtml = reasoningSentences.length > 1 
            ? `<ul class="list-disc list-inside text-gray-700 mb-4 space-y-1">${reasoningSentences.map(s => `<li>${escapeHtml(s.trim())}.</li>`).join('')}</ul>`
            : `<p class="text-gray-700 mb-4">${escapeHtml(content.reasoning)}</p>`;
        
        div.innerHTML = `
            <h2 class="text-3xl font-bold text-amber-700 mb-3">Your question needs clarification</h2>
            ${reasoningHtml}
            <div class="space-y-3">
                <p class="text-sm font-medium text-gray-700 mb-2">Suggested rewrites (click to use):</p>
                ${content.clarification_options.map((option, index) => `
                    <button 
                        class="clarification-option w-full text-left px-4 py-3 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        data-rewrite="${escapeHtml(option.rewritten_question)}"
                    >
                        <div class="font-semibold text-blue-900 mb-1">${index + 1}. ${escapeHtml(option.label)}</div>
                        <div class="text-blue-800 text-sm">${escapeHtml(option.rewritten_question)}</div>
                    </button>
                `).join('')}
            </div>
        `;
        
        // Attach click handlers to clarification options
        div.querySelectorAll('.clarification-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const rewrite = btn.getAttribute('data-rewrite');
                populateInputWithRewrite(rewrite);
            });
        });
    } else if (subtype === 'confirmation') {
        // CONFIRMATION response type
        div.className = 'bg-green-50 border-2 border-green-500 rounded-lg p-6 mb-4';
        div.innerHTML = `
            <div class="flex items-start gap-4 mb-6">
                <div class="flex-shrink-0">
                    <div class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                        <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" stroke-width="4" viewBox="0 0 24 24">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                </div>
                <div class="flex-1 pt-2">
                    <h2 class="text-3xl font-bold text-green-700 mb-2">Your question is well-structured</h2>
                    <p class="text-gray-800 text-lg">This question is clear and specific enough for research purposes.</p>
                </div>
            </div>
            <div class="bg-white border border-gray-300 rounded-lg p-5">
                <p class="text-xs font-bold text-gray-600 mb-3 uppercase tracking-wider">Confirmed Prompt</p>
                <p class="text-gray-900 text-base leading-relaxed">"${escapeHtml(content)}"</p>
            </div>
        `;
    } else if (subtype === 'out_of_scope') {
        // OUT_OF_SCOPE response type
        div.className = 'bg-white border border-gray-200 rounded-lg p-6 mb-4';
        div.innerHTML = `
            <h2 class="text-xl font-semibold text-amber-700 mb-3">Out of scope</h2>
            <p class="text-gray-700">${escapeHtml(content)}</p>
        `;
    } else {
        // Fallback for unexpected content structure
        div.className = 'bg-white border border-gray-200 rounded-lg p-6 mb-4';
        div.innerHTML = `<p class="text-gray-700">${escapeHtml(typeof content === 'string' ? content : JSON.stringify(content))}</p>`;
    }
    
    return div;
}

/**
 * Create healthcare reminder block (blue info box)
 */
function createHealthcareReminder(content) {
    const div = document.createElement('div');
    div.className = 'bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg mb-4';
    div.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                </svg>
            </div>
            <div class="ml-3">
                <p class="text-sm text-blue-800">${escapeHtml(content)}</p>
            </div>
        </div>
    `;
    return div;
}

/**
 * Create closing message block (result footer - NOT page footer)
 * Styling varies based on message type (both get prominent styling, different colors)
 */
function createClosingMessage(content) {
    const div = document.createElement('div');
    
    // Check message type and apply appropriate styling
    const isSuccessMessage = content.includes('can be used safely');
    const isClarificationMessage = content.includes('Pick or revise');
    
    if (isSuccessMessage) {
        // Prominent green styling for confirmation/success state
        div.className = 'bg-green-100 border-l-4 border-green-600 p-4 rounded-r-lg mb-4';
        div.innerHTML = `<p class="text-base font-semibold text-green-800">${escapeHtml(content)}</p>`;
    } else if (isClarificationMessage) {
        // Prominent amber styling for clarification state (actionable, not error)
        div.className = 'bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg mb-4';
        div.innerHTML = `<p class="text-base font-semibold text-amber-800">${escapeHtml(content)}</p>`;
    } else {
        // Fallback styling (should rarely be used)
        div.className = 'bg-gray-100 border-l-4 border-gray-400 p-4 rounded-r-lg mb-4';
        div.innerHTML = `<p class="text-base font-semibold text-gray-700">${escapeHtml(content)}</p>`;
    }
    
    return div;
}

/**
 * Create "Ask Another Question" button
 */
function createAskAnotherButton() {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'w-full mt-6 bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2';
    btn.textContent = 'Ask Another Question';
    
    btn.addEventListener('click', () => {
        resetUI();
    });
    
    return btn;
}

// ============================================================================
// UI State Management
// ============================================================================

/**
 * Populate input field with a clarification rewrite option
 */
function populateInputWithRewrite(rewrite) {
    textarea.value = rewrite;
    updateWordCounter();
    
    // Hide results and scroll to form
    hideResultArea();
    
    // Focus on textarea
    textarea.focus();
    
    // Scroll to form
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Reset UI to initial state (clear form and results)
 */
function resetUI() {
    // Clear textarea
    textarea.value = '';
    updateWordCounter();
    
    // Hide result area
    hideResultArea();
    
    // Hide validation error
    hideValidationError();
    
    // Focus on textarea
    textarea.focus();
    
    // Scroll to top
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
 * (Belt-and-suspenders: backend should also sanitize, but client-side defense is good practice)
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Initialization
// ============================================================================

// Initialize word counter on page load
updateWordCounter();
