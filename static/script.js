// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat functionality if on chat page
    if (document.getElementById('chat-form')) {
        initChat();
    }
    
    // Initialize admin dashboard if on admin page
    if (document.getElementById('admin-dashboard')) {
        initAdminDashboard();
    }
    
    // Initialize tabs if present
    const tabEls = document.querySelectorAll('button[data-bs-toggle="pill"]');
    if (tabEls.length > 0) {
        tabEls.forEach(tabEl => {
            tabEl.addEventListener('shown.bs.tab', function (event) {
                const targetId = event.target.getAttribute('data-bs-target');
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('active', 'show');
                });
                document.querySelector(targetId).classList.add('active', 'show');
            });
        });
    }
});

// Chat functionality
function initChat() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    
    // Add event listener to chat form
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage('user', message);
        
        // Clear input
        messageInput.value = '';
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Send request to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add bot response to chat
            if (data.error) {
                addMessage('bot', 'Sorry, an error occurred: ' + data.error);
            } else {
                addMessage('bot', data.response);
            }
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add error message
            addMessage('bot', 'Sorry, an error occurred while processing your request.');
            console.error('Error:', error);
            
            // Scroll to bottom
            scrollToBottom();
        });
    });
    
    // Function to add a message to the chat
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        
        // Handle markdown in bot messages
        if (sender === 'bot') {
            // Convert markdown tables to HTML
            text = convertMarkdownTables(text);
            
            // Convert other markdown elements
            text = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
        }
        
        messageDiv.innerHTML = text;
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Function to convert markdown tables to HTML
    function convertMarkdownTables(text) {
        // Check if the text contains a table
        if (!text.includes('|')) return text;
        
        const lines = text.split('\n');
        let inTable = false;
        let tableHTML = '<table class="table table-dark table-striped">';
        let result = [];
        
        for (let line of lines) {
            if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
                if (!inTable) {
                    inTable = true;
                }
                
                // Parse the table row
                const cells = line.split('|').filter(cell => cell.trim() !== '');
                
                // Check if this is a separator line
                if (cells.every(cell => cell.trim().replace(/-/g, '') === '')) {
                    continue;
                }
                
                // Add row to table
                tableHTML += '<tr>';
                for (let cell of cells) {
                    tableHTML += `<td>${cell.trim()}</td>`;
                }
                tableHTML += '</tr>';
            } else {
                if (inTable) {
                    tableHTML += '</table>';
                    result.push(tableHTML);
                    tableHTML = '<table class="table table-dark table-striped">';
                    inTable = false;
                }
                result.push(line);
            }
        }
        
        if (inTable) {
            tableHTML += '</table>';
            result.push(tableHTML);
        }
        
        return result.join('\n');
    }
    
    // Function to add typing indicator
    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'bot-message', 'typing-indicator');
        typingDiv.innerHTML = 'Thinking<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
        return typingDiv;
    }
    
    // Function to scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Admin dashboard functionality
function initAdminDashboard() {
    // Initialize chart if canvas exists
    const chartCanvas = document.getElementById('chatActivityChart');
    if (chartCanvas) {
        const labels = JSON.parse(chartCanvas.getAttribute('data-labels'));
        const data = JSON.parse(chartCanvas.getAttribute('data-values'));
        
        new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Chat Activity',
                    data: data,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    // Initialize student list functionality
    const studentListContainer = document.getElementById('student-list');
    if (studentListContainer) {
        loadStudentList();
    }
    
    // Initialize chat logs functionality
    const chatLogsContainer = document.getElementById('chat-logs');
    if (chatLogsContainer) {
        loadChatLogs();
    }
}

// Function to load student list
function loadStudentList() {
    fetch('/admin/students')
        .then(response => response.json())
        .then(students => {
            const studentListContainer = document.getElementById('student-list');
            
            if (students.length === 0) {
                studentListContainer.innerHTML = '<p>No students found.</p>';
                return;
            }
            
            let html = `
                <table class="table table-dark table-striped">
                    <thead>
                        <tr>
                            <th>Serial No</th>
                            <th>Roll No</th>
                            <th>Name</th>
                            <th>Major</th>
                            <th>GPA</th>
                            <th>Attendance</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            students.forEach(student => {
                html += `
                    <tr>
                        <td>${student.serial_no}</td>
                        <td>${student.roll_no}</td>
                        <td>${student.name}</td>
                        <td>${student.major}</td>
                        <td>${student.current_gpa}</td>
                        <td>${student.attendance_percentage}%</td>
                        <td>
                            <button class="btn btn-sm btn-danger delete-student" data-id="${student.id}">Delete</button>
                        </td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            `;
            
            studentListContainer.innerHTML = html;
            
            // Add event listeners to delete buttons
            document.querySelectorAll('.delete-student').forEach(button => {
                button.addEventListener('click', function() {
                    const studentId = this.getAttribute('data-id');
                    if (confirm('Are you sure you want to delete this student?')) {
                        deleteStudent(studentId);
                    }
                });
            });
        })
        .catch(error => {
            console.error('Error loading students:', error);
            document.getElementById('student-list').innerHTML = 
                '<div class="alert alert-danger">Error loading student data.</div>';
        });
}

// Function to delete a student
function deleteStudent(studentId) {
    fetch(`/admin/students/${studentId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload student list
            loadStudentList();
            // Show success message
            alert(data.message);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting student:', error);
        alert('An error occurred while deleting the student.');
    });
}

// Function to load chat logs
function loadChatLogs() {
    fetch('/admin/chatlogs')
        .then(response => response.json())
        .then(logs => {
            const chatLogsContainer = document.getElementById('chat-logs');
            
            if (logs.length === 0) {
                chatLogsContainer.innerHTML = '<p>No chat logs found.</p>';
                return;
            }
            
            let html = `
                <table class="table table-dark table-striped">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>User Type</th>
                            <th>User ID</th>
                            <th>Query</th>
                            <th>Response</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            logs.forEach(log => {
                html += `
                    <tr>
                        <td>${log.timestamp}</td>
                        <td>${log.user_type}</td>
                        <td>${log.user_id}</td>
                        <td>${log.query}</td>
                        <td>${log.response.length > 100 ? log.response.substring(0, 100) + '...' : log.response}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            `;
            
            chatLogsContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading chat logs:', error);
            document.getElementById('chat-logs').innerHTML = 
                '<div class="alert alert-danger">Error loading chat logs.</div>';
        });
}
