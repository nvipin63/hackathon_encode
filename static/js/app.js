// API endpoint
const API_URL = 'http://localhost:5000/api/analyze';

// DOM elements
const journalForm = document.getElementById('journalForm');
const analyzeBtn = document.getElementById('analyzeBtn');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const retryBtn = document.getElementById('retryBtn');

// Form inputs
const journalEntry = document.getElementById('journalEntry');
const dietPreference = document.getElementById('dietPreference');
const energyLevel = document.getElementById('energyLevel');

// Result containers
const triggersContent = document.getElementById('triggersContent');
const recommendationContent = document.getElementById('recommendationContent');
const logisticsContent = document.getElementById('logisticsContent');
const errorMessage = document.getElementById('errorMessage');

// Agent step elements
const agentSteps = {
    router: document.querySelector('[data-agent="router"]'),
    detective: document.querySelector('[data-agent="detective"]'),
    nutritionist: document.querySelector('[data-agent="nutritionist"]'),
    logistics: document.querySelector('[data-agent="logistics"]')
};

/**
 * Show/hide sections
 */
function showSection(section) {
    [progressSection, resultsSection, errorSection].forEach(s => {
        s.style.display = 'none';
    });
    if (section) {
        section.style.display = 'block';
        section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Update agent step status
 */
function updateAgentStep(agent, status) {
    const step = agentSteps[agent];
    if (!step) return;

    // Remove all status classes
    step.classList.remove('active', 'complete');

    if (status === 'active') {
        step.classList.add('active');
        const indicator = step.querySelector('.step-indicator');
        indicator.innerHTML = '<div class="loading-spinner"></div>';
    } else if (status === 'complete') {
        step.classList.add('complete');
        const indicator = step.querySelector('.step-indicator');
        indicator.innerHTML = '<span class="complete">✓</span>';
    }
}

/**
 * Simulate agent progress (for better UX)
 */
async function simulateAgentProgress() {
    const agents = ['router', 'detective', 'nutritionist', 'logistics'];

    for (const agent of agents) {
        updateAgentStep(agent, 'active');
        // Wait a bit for visual effect
        await new Promise(resolve => setTimeout(resolve, agent === 'router' ? 500 : 800));
        updateAgentStep(agent, 'complete');
    }
}

/**
 * Format and display triggers
 */
function displayTriggers(triggers) {
    if (!triggers || triggers.length === 0) {
        triggersContent.innerHTML = '<p>No specific triggers detected in your journal entry.</p>';
        return;
    }

    const triggerList = document.createElement('div');
    triggerList.className = 'trigger-list';

    triggers.forEach(trigger => {
        const tag = document.createElement('span');
        tag.className = 'trigger-tag';
        tag.textContent = trigger;
        triggerList.appendChild(tag);
    });

    triggersContent.innerHTML = '<p>We detected the following triggers that may influence your eating patterns:</p>';
    triggersContent.appendChild(triggerList);
}

/**
 * Format and display recommendation with markdown support
 */
function displayRecommendation(recommendation) {
    if (!recommendation) {
        recommendationContent.innerHTML = '<p>No recommendation available.</p>';
        return;
    }

    // Split into lines
    const lines = recommendation.split('\n');
    let html = '';
    let inList = false;
    let inTable = false;
    let tableHeaders = [];
    let tableRows = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // Skip empty lines
        if (!trimmed) {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            if (inTable) {
                html += buildHtmlTable(tableHeaders, tableRows);
                inTable = false;
                tableHeaders = [];
                tableRows = [];
            }
            continue;
        }

        // Check if this is a table line (contains | characters)
        if (trimmed.includes('|') && !trimmed.startsWith('#')) {
            if (inList) {
                html += '</ul>';
                inList = false;
            }

            // Check if this is a separator line (e.g., |---|---|)
            if (trimmed.match(/^\|[\s\-:]+\|/)) {
                inTable = true;
                continue; // Skip separator line
            }

            // Parse table row
            const cells = trimmed
                .split('|')
                .map(cell => cell.trim())
                .filter(cell => cell.length > 0);

            if (!inTable) {
                // This is the header row
                tableHeaders = cells;
                inTable = true;
            } else {
                // This is a data row
                tableRows.push(cells);
            }
            continue;
        }

        // If we were in a table and hit a non-table line, close the table
        if (inTable) {
            html += buildHtmlTable(tableHeaders, tableRows);
            inTable = false;
            tableHeaders = [];
            tableRows = [];
        }

        // Headings
        if (trimmed.startsWith('#### ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h4>${trimmed.substring(5)}</h4>`;
        } else if (trimmed.startsWith('### ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h3>${trimmed.substring(4)}</h3>`;
        } else if (trimmed.startsWith('## ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h3>${trimmed.substring(3)}</h3>`;
        } else if (trimmed.startsWith('# ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h2>${trimmed.substring(2)}</h2>`;
        }
        // Numbered lists
        else if (trimmed.match(/^\d+\.\s/)) {
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            const content = trimmed.replace(/^\d+\.\s/, '').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            html += `<li>${content}</li>`;
        }
        // Bullet points
        else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            const content = trimmed.substring(2).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            html += `<li>${content}</li>`;
        }
        // Regular paragraph
        else {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            // Apply bold/italic
            const formatted = trimmed
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>');
            html += `<p>${formatted}</p>`;
        }
    }

    // Close any remaining open elements
    if (inList) {
        html += '</ul>';
    }
    if (inTable) {
        html += buildHtmlTable(tableHeaders, tableRows);
    }

    recommendationContent.innerHTML = html;
}

/**
 * Build an HTML table from headers and rows
 */
function buildHtmlTable(headers, rows) {
    if (headers.length === 0 && rows.length === 0) {
        return '';
    }

    let table = '<table class="meal-plan-table">';

    // Add header
    if (headers.length > 0) {
        table += '<thead><tr>';
        headers.forEach(header => {
            table += `<th>${header}</th>`;
        });
        table += '</tr></thead>';
    }

    // Add rows
    if (rows.length > 0) {
        table += '<tbody>';
        rows.forEach(row => {
            table += '<tr>';
            row.forEach(cell => {
                table += `<td>${cell}</td>`;
            });
            table += '</tr>';
        });
        table += '</tbody>';
    }

    table += '</table>';
    return table;
}

/**
 * Extract and display logistics
 */
function displayLogistics(completeResponse) {
    if (!completeResponse) {
        logisticsContent.innerHTML = '<p>No logistics information available.</p>';
        return;
    }

    // Find logistics section
    const markers = ['📋 LOGISTICS PLAN', 'LOGISTICS PLAN'];
    let startIndex = -1;

    for (const marker of markers) {
        startIndex = completeResponse.indexOf(marker);
        if (startIndex > -1) break;
    }

    if (startIndex === -1) {
        logisticsContent.innerHTML = `
            <div>
                <h4>📅 Meal Prep Plan</h4>
                <p>Plan to prep your meal this Sunday at 5:00 PM</p>
                <h4 style="margin-top: 1rem;">🛒 Next Steps</h4>
                <p>1. Review the meal recommendation above for ingredients<br>
                2. Create your shopping list<br>
                3. Set a reminder for meal prep day</p>
            </div>
        `;
        return;
    }

    // Extract logistics text
    const logisticsText = completeResponse.substring(startIndex);
    const lines = logisticsText.split('\n');
    let html = '<div class="logistics-formatted">';

    for (let line of lines) {
        const trimmed = line.trim();

        if (trimmed.includes('LOGISTICS PLAN')) {
            html += `<h3 style="margin-top: 0;">${trimmed.replace(/=/g, '')}</h3>`;
        } else if (trimmed.match(/^(🛒|📅|💡|🎯|📦|🍽️|✅)/)) {
            html += `<h4 style="margin-top: 1rem;">${trimmed}</h4>`;
        } else if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.match(/^\d+\./)) {
            html += `<p style="margin-left: 1rem;">${trimmed}</p>`;
        } else if (trimmed && !trimmed.match(/^=+$/)) {
            html += `<p>${trimmed}</p>`;
        }
    }

    html += '</div>';
    logisticsContent.innerHTML = html;
}

/**
 * Show error message
 */
function displayError(error) {
    errorMessage.textContent = error;
    showSection(errorSection);
}

/**
 * Handle form submission
 */
async function handleSubmit(e) {
    e.preventDefault();

    // Validate input
    const journal = journalEntry.value.trim();
    if (!journal) {
        displayError('Please enter your journal entry.');
        return;
    }

    // Show progress section
    showSection(progressSection);

    // Disable form
    analyzeBtn.disabled = true;
    analyzeBtn.querySelector('.btn-text').textContent = 'Analyzing...';

    // Reset agent steps
    Object.keys(agentSteps).forEach(agent => {
        updateAgentStep(agent, 'pending');
    });

    try {
        // Start progress animation
        const progressPromise = simulateAgentProgress();

        // Make API request
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                journal_entry: journal,
                user_profile: {
                    name: 'User',
                    diet: dietPreference.value,
                    allergies: []
                },
                health_data: {
                    glucose_trend: 'Normal',
                    energy_level: energyLevel.value
                }
            })
        });

        // Wait for progress animation to complete
        await progressPromise;

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Analysis failed');
        }

        // Display results
        displayTriggers(data.results.detected_triggers);
        displayRecommendation(data.results.final_plan);
        displayLogistics(data.results.complete_response);

        // Show results section
        showSection(resultsSection);

    } catch (error) {
        console.error('Error:', error);
        displayError(`Unable to analyze your journal: ${error.message}. Please make sure the server is running.`);
    } finally {
        // Re-enable form
        analyzeBtn.disabled = false;
        analyzeBtn.querySelector('.btn-text').textContent = 'Analyze My Journal';
    }
}

/**
 * Reset form and start new analysis
 */
function resetForm() {
    journalForm.reset();
    showSection(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Retry after error
 */
function retryAnalysis() {
    showSection(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Event listeners
journalForm.addEventListener('submit', handleSubmit);
newAnalysisBtn.addEventListener('click', resetForm);
retryBtn.addEventListener('click', retryAnalysis);

// Add smooth scroll behavior to the page
document.documentElement.style.scrollBehavior = 'smooth';

// Log ready state
console.log('✅ NutriMind Frontend Ready');
console.log('📡 API Endpoint:', API_URL);
