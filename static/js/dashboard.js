
//  Tab Switching

function showTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));

  const tabButton = document.querySelector(`[data-tab="${tabId}"]`);
  const tabContent = document.getElementById(`${tabId}-tab`);

  if (tabButton) tabButton.classList.add('active');
  if (tabContent) tabContent.classList.add('active');

  if (tabId === 'analytics') {
    initializeAnalytics();
  }
}


// Modal Controls
function openTaskModal() {
  document.getElementById('taskModal')?.classList.add('show');
}

function closeTaskModal() {
  document.getElementById('taskModal')?.classList.remove('show');
  resetModalToAddMode();
}

function resetModalToAddMode() {
  const form = document.getElementById('taskForm');
  if (!form) return;

  document.querySelector('.modal-header h3').textContent = '✏️ Add New Task';
  form.action = '/add-task';
  form.reset();

  document.getElementById('priority').value = 'Medium';
  document.getElementById('completed').value = 'False';
  document.querySelector('.btn-primary').innerHTML = '<i class="fas fa-save"></i> Save Task';
}

window.addEventListener('click', e => {
  const modal = document.getElementById('taskModal');
  if (e.target === modal) closeTaskModal();
});


// Edit Task
function editTask(taskId) {
  const card = document.querySelector(`[data-task-id="${taskId}"]`);
  if (!card) return;

  document.getElementById('title').value = card.querySelector('.task-title')?.textContent || '';
  document.getElementById('description').value = card.querySelector('.task-desc')?.textContent || '';
  document.getElementById('priority').value = card.querySelector('.priority-badge')?.textContent || 'Medium';

  const dueText = card.querySelector('.task-info p:nth-child(1)')?.textContent || '';
  const timeText = card.querySelector('.task-info p:nth-child(2)')?.textContent || '';
  const isCompleted = card.querySelector('.status-complete') !== null;

  const dueDate = dueText.replace('Due: ', '').trim();
  const estTime = timeText.replace('Estimated: ', '').replace(' hrs', '').trim();

  document.getElementById('due_date').value = dueDate !== 'No due date' ? dueDate : '';
  document.getElementById('time_spent').value = estTime;
  document.getElementById('completed').value = isCompleted ? 'True' : 'False';

  document.querySelector('.modal-header h3').textContent = '✏️ Edit Task';
  document.getElementById('taskForm').action = `/edit-task/${taskId}`;
  document.querySelector('.btn-primary').innerHTML = '<i class="fas fa-save"></i> Update Task';

  openTaskModal();
}


// Task Filter & Sort
function filterTasks() {
  const query = document.getElementById('task-search').value.toLowerCase();
  document.querySelectorAll('.task-card').forEach(card => {
    const title = card.querySelector('h4')?.innerText.toLowerCase() || '';
    const desc = card.querySelector('p')?.innerText.toLowerCase() || '';
    card.style.display = title.includes(query) || desc.includes(query) ? 'block' : 'none';
  });
}

function applySort() {
  const type = document.getElementById('filter-dropdown').value;
  const container = document.getElementById('task-list');
  const tasks = Array.from(container.getElementsByClassName('task-card'));

  const priorityOrder = { 'High': 1, 'Medium': 2, 'Low': 3 };

  tasks.sort((a, b) => {
    if (type === 'newest') return new Date(b.dataset.created) - new Date(a.dataset.created);
    if (type === 'oldest') return new Date(a.dataset.created) - new Date(b.dataset.created);
    if (['high', 'medium', 'low'].includes(type)) {
      return priorityOrder[a.dataset.priority] - priorityOrder[b.dataset.priority];
    }
    return 0;
  });

  tasks.forEach(task => container.appendChild(task));
}


// Time Tracking
const timers = {};
const intervals = {};

function formatTime(secs) {
  const h = String(Math.floor(secs / 3600)).padStart(2, '0');
  const m = String(Math.floor((secs % 3600) / 60)).padStart(2, '0');
  const s = String(secs % 60).padStart(2, '0');
  return `${h}:${m}:${s}`;
}

function startTimer(taskId) {
  if (!timers[taskId]) timers[taskId] = 0;

  if (!intervals[taskId]) {
    intervals[taskId] = setInterval(() => {
      timers[taskId]++;
      const timerEl = document.getElementById(`timer-${taskId}`);
      if (timerEl) timerEl.innerText = formatTime(timers[taskId]);
    }, 1000);
  }
}

function pauseTimer(taskId) {
  if (intervals[taskId]) {
    clearInterval(intervals[taskId]);
    intervals[taskId] = null;
  }
}

function logTime(taskId) {
  pauseTimer(taskId);
  const hours = (timers[taskId] / 3600).toFixed(2);

  fetch(`/log-time/${taskId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actual_time_spent: hours })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message || 'Time logged!');
      location.reload();
    })
    .catch(() => alert('Failed to log time.'));
}


// Analytics (Chart.js)
function initializeAnalytics() {
  const parse = id => JSON.parse(document.getElementById(id)?.textContent || '[]');

  new Chart(document.getElementById('taskCreationChart'), {
    type: 'bar',
    data: {
      labels: parse('dailyLabels'),
      datasets: [{
        label: 'Tasks per Day',
        data: parse('dailyData'),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  });

  new Chart(document.getElementById('priorityChart'), {
    type: 'doughnut',
    data: {
      labels: Object.keys(parse('priorityData')),
      datasets: [{
        data: Object.values(parse('priorityData')),
        backgroundColor: ['#ff6384', '#ffcd56', '#4bc0c0']
      }]
    },
    options: { responsive: true }
  });

  new Chart(document.getElementById('completionChart'), {
    type: 'pie',
    data: {
      labels: Object.keys(parse('completionData')),
      datasets: [{
        data: Object.values(parse('completionData')),
        backgroundColor: ['#36a2eb', '#ff9f40']
      }]
    },
    options: { responsive: true }
  });

  new Chart(document.getElementById('timeChart'), {
    type: 'bar',
    data: {
      labels: parse('timeLabels'),
      datasets: [
        {
          label: 'Estimated Hours',
          data: parse('estimatedTimes'),
          backgroundColor: 'rgba(153, 102, 255, 0.6)'
        },
        {
          label: 'Actual Hours',
          data: parse('actualTimes'),
          backgroundColor: 'rgba(255, 99, 132, 0.6)'
        }
      ]
    },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  });
}


// Report Downloads
function downloadPDFReport() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.text("Task Report", 14, 14);

  const rows = [];
  document.querySelectorAll("#reports-tab tbody tr").forEach(tr => {
    const row = Array.from(tr.children).map(td => td.innerText);
    rows.push(row);
  });

  doc.autoTable({
    head: [['Title', 'Status', 'Priority', 'Due Date', 'Est Time', 'Act Time']],
    body: rows,
    startY: 20
  });

  doc.save("task_report.pdf");
}

function downloadCSVReport() {
  let csv = "Title,Status,Priority,Due Date,Estimated Time,Actual Time\n";

  document.querySelectorAll("#reports-tab tbody tr").forEach(tr => {
    const row = Array.from(tr.children).map(td => `"${td.innerText}"`).join(",");
    csv += row + "\n";
  });

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'task_report.csv';
  a.click();
  URL.revokeObjectURL(url);
}


// Default Tab Load
document.addEventListener('DOMContentLoaded', () => showTab('tasks'));
