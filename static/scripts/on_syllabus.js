// Check books directory status on page load
        window.addEventListener('load', function() {
            checkBooks();
            setupFileUpload();
            document.getElementById('question').focus();
        });

        function setupFileUpload() {
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-upload');
            
            // Handle file input change
            fileInput.addEventListener('change', function(e) {
                displaySelectedFiles(e.target.files);
            });
            
            // Drag and drop handlers with better visual feedback
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
            
            dropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            });
            
            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                fileInput.files = files;
                displaySelectedFiles(files);
            });
        }
        
        function displaySelectedFiles(files) {
            const selectedFilesDiv = document.getElementById('selected-files');
            const fileList = document.getElementById('file-list');
            
            if (files.length > 0) {
                const fileItems = Array.from(files).map(file => 
                    `<li><span>📄</span> ${file.name} <span style="color: var(--text-muted);">(${(file.size / 1024).toFixed(1)} KB)</span></li>`
                ).join('');
                
                fileList.innerHTML = fileItems;
                selectedFilesDiv.style.display = 'block';
            } else {
                selectedFilesDiv.style.display = 'none';
            }
        }

        async function uploadBooks() {
            const fileInput = document.getElementById('file-upload');
            const uploadStatus = document.getElementById('upload-status');
            const files = fileInput.files;
            
            if (files.length === 0) {
                uploadStatus.className = 'upload-status error';
                uploadStatus.innerHTML = '⚠️ Please select at least one file to upload.';
                uploadStatus.style.display = 'block';
                return;
            }
            
            // Show upload progress
            uploadStatus.className = 'upload-status info';
            uploadStatus.innerHTML = `<span>📤</span> Uploading ${files.length} file(s)... Please wait.`;
            uploadStatus.style.display = 'block';
            
            try {
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
                
                const response = await fetch('/upload-books', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    uploadStatus.className = 'upload-status success';
                    uploadStatus.innerHTML = `
                        <strong>✅ Upload successful!</strong>
                        <br><span>📚</span> Uploaded files: ${result.uploaded_files.join(', ')}
                        ${result.skipped_files.length > 0 ? `<br><span>⚠️</span> Skipped files: ${result.skipped_files.join(', ')}` : ''}
                    `;
                    
                    // Clear the file input and hide selected files
                    fileInput.value = '';
                    document.getElementById('selected-files').style.display = 'none';
                    
                    // Refresh books status
                    setTimeout(checkBooks, 1000);
                } else {
                    uploadStatus.className = 'upload-status error';
                    uploadStatus.innerHTML = `<strong>❌ Upload failed:</strong> ${result.error}`;
                }
            } catch (error) {
                uploadStatus.className = 'upload-status error';
                uploadStatus.innerHTML = `<strong>❌ Upload error:</strong> ${error.message}`;
            }
        }

        async function checkBooks() {
            try {
                const response = await fetch('/check-books');
                const data = await response.json();
                const statusDiv = document.getElementById('books-status');
                
                if (data.exists && data.files.length > 0) {
                    statusDiv.className = 'books-status success';
                    statusDiv.innerHTML = `
                        <strong>✅ Your knowledge library is ready!</strong>
                        <p>Found ${data.files.length} files in your books directory. You can now ask questions about your materials.</p>
                        <div class="file-list">
                            ${data.files.map(file => `
                                <div class="file-item">
                                    <span>📄</span> ${file.name} <span style="color: var(--text-muted);">(${file.type}) - ${(file.size / 1024).toFixed(1)} KB</span>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else if (data.exists) {
                    statusDiv.className = 'books-status error';
                    statusDiv.innerHTML = `
                        <strong>⚠️ Library found but empty</strong>
                        <p>Your books directory exists but contains no supported files. Please upload your study materials using the upload section above.</p>
                        <p><strong>Supported formats:</strong> Text files (.txt), Markdown (.md), PDF (.pdf), Word documents (.docx, .doc)</p>
                    `;
                } else {
                    statusDiv.className = 'books-status error';
                    statusDiv.innerHTML = `
                        <strong>📁 No library found</strong>
                        <p>Let's get you started! Upload your textbooks, lecture notes, and study materials using the upload section above to create your personalized knowledge library.</p>
                        <p><strong>Tip:</strong> The more materials you upload, the better I can help you with curriculum-specific questions!</p>
                    `;
                }
            } catch (error) {
                const statusDiv = document.getElementById('books-status');
                statusDiv.className = 'books-status error';
                statusDiv.innerHTML = `<strong>❌ Error checking library:</strong> ${error.message}`;
            }
        }

        async function askQuestion() {
            const question = document.getElementById('question').value;
            if (!question.trim()) {
                alert('💡 Please enter a question about your study materials!');
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
                        mode: "on-syllabus"
                    })
                });
                
                const data = await response.json();
                
                // Debug: Log the response data
                console.log('Response data:', data);
                
                // Render markdown content
                const markdownAnswer = marked.parse(data.answer);
                document.getElementById('answer').innerHTML = markdownAnswer;
                
                // Handle sources with better formatting
                const sourcesDiv = document.getElementById('sources');
                const sourcesList = document.getElementById('sources-list');
                
                if (data.sources && data.sources.length > 0) {
                    sourcesList.innerHTML = data.sources.map(source => 
                        `<li><span>📖</span> ${source}</li>`
                    ).join('');
                    sourcesDiv.style.display = 'block';
                } else {
                    sourcesDiv.style.display = 'none';
                }
                
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
                console.error('Error details:', error);
                document.getElementById('answer').innerHTML = `
                    <div style="color: var(--error-text); padding: 20px; background: var(--error-bg); border-radius: var(--radius-md); border: 1px solid var(--error-border);">
                        <strong>⚠️ Oops! Something went wrong:</strong> ${error.message}
                        <br><br>
                        <strong>💡 Troubleshooting Tips:</strong>
                        <ul>
                            <li>📚 Make sure you have uploaded files to your library</li>
                            <li>📋 Check that your files are in supported formats (.txt, .md, .pdf, .docx)</li>
                            <li>🔄 Try refreshing your library status</li>
                        </ul>
                    </div>
                `;
                document.getElementById('agent-details').innerHTML = '';
                document.getElementById('sources').style.display = 'none';
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
        
        // Add visual feedback for typing
        document.getElementById('question').addEventListener('input', function(e) {
            const button = document.querySelector('button:not(.secondary)');
            if (e.target.value.trim()) {
                button.style.transform = 'scale(1.02)';
                button.style.boxShadow = 'var(--glow-green)';
            } else {
                button.style.transform = '';
                button.style.boxShadow = '';
            }
        });