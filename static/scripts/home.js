async function askQuestion() {
            const question = document.getElementById('question').value;
            if (!question.trim()) {
                alert('💡 Please enter a question to get started!');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        question: question,
                        mode: "off-syllabus"
                    })
                });
                
                const data = await response.json();
                
                // Render markdown content
                const markdownAnswer = marked.parse(data.answer);
                document.getElementById('answer').innerHTML = markdownAnswer;
                
                // Build agent info with better formatting
                let agentInfo = `<strong>Handled by:</strong> ${data.agent_used}`;
                if (data.tools_used && data.tools_used.length > 0) {
                    agentInfo += ` | <strong>🛠️ Tools used:</strong> ${data.tools_used.join(', ')}`;
                }
                
                document.getElementById('agent-details').innerHTML = agentInfo;
                document.getElementById('response').style.display = 'block';
                
                // Smooth scroll to response
                document.getElementById('response').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
                
            } catch (error) {
                document.getElementById('answer').innerHTML = `
                    <div style="color: var(--error-text); padding: 20px; background: var(--error-bg); border-radius: var(--radius-md); border: 1px solid var(--error-border);">
                        <strong>⚠️ Oops! Something went wrong:</strong> ${error.message}
                        <br><br>
                        <strong>💡 Please try again or contact support if the problem persists.</strong>
                    </div>
                `;
                document.getElementById('agent-details').innerHTML = '';
                document.getElementById('response').style.display = 'block';
            }
            
            document.getElementById('loading').style.display = 'none';
        }
        
        // Enhanced enter key handling
        document.getElementById('question').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askQuestion();
            }
        });
        
        // Focus on input when page loads
        window.addEventListener('load', function() {
            document.getElementById('question').focus();
        });
        
        // Add some visual feedback for typing
        document.getElementById('question').addEventListener('input', function(e) {
            const button = document.querySelector('button');
            if (e.target.value.trim()) {
                button.style.transform = 'scale(1.02)';
                button.style.boxShadow = 'var(--glow-green)';
            } else {
                button.style.transform = '';
                button.style.boxShadow = '';
            }
        });