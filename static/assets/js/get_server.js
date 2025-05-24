const url = '/api/servers';
fetch(url)
    .then(response => response.json())
    .then(jsonData => {
        if (jsonData.status == 'error' || jsonData.status == 'fixed') {
            alert(jsonData.message);
            return;
        }
        const memoryTag = document.getElementById('memory');
        const memorytextToUpdate = `${jsonData.now.memory}/${jsonData.resource.memory} MB`;
        memoryTag.textContent = memorytextToUpdate;

        const cpuTag = document.getElementById('cpu');
        const cputextToUpdate = `${jsonData.now.cpu}/${jsonData.resource.cpu}%`;
        cpuTag.textContent = cputextToUpdate;

        const diskTag = document.getElementById('disk');
        const disktextToUpdate = `${jsonData.now.disk}/${jsonData.resource.disk} MB`;
        diskTag.textContent = disktextToUpdate;

        const serversTag = document.getElementById('servers');
        const serverstextToUpdate = `${jsonData.now.servers}/${jsonData.resource.servers}`;
        serversTag.textContent = serverstextToUpdate;

        const serverTableBody = document.getElementById('serverTableBody');

        for (const serverId in jsonData.server) {
            const server = jsonData.server[serverId];

            const row = document.createElement('tr');
            row.classList.add('text-gray-700', 'dark:text-gray-400');

            const nameCell = document.createElement('td');
            nameCell.classList.add('px-4', 'py-3');
            nameCell.innerHTML = `
                      <div class="flex items-center text-sm">
                        <div>
                          <p class="font-semibold">${server.name}</p>
                          <p class="text-xs text-gray-600 dark:text-gray-400">${server.description}</p>
                        </div>
                      </div>
                    `;
            row.appendChild(nameCell);

            const cpuCell = document.createElement('td');
            cpuCell.classList.add('px-4', 'py-3', 'text-sm');
            cpuCell.textContent = `${server.cpu}%`;
            row.appendChild(cpuCell);

            const memoryCell = document.createElement('td');
            memoryCell.classList.add('px-4', 'py-3', 'text-sm');
            memoryCell.textContent = `${server.memory}MB`;
            row.appendChild(memoryCell);

            const diskCell = document.createElement('td');
            diskCell.classList.add('px-4', 'py-3', 'text-sm');
            diskCell.textContent = `${server.disk}MB`;
            row.appendChild(diskCell);

            const actionCell = document.createElement('td');
            actionCell.classList.add('px-4', 'py-3', 'text-xs');
            actionCell.innerHTML = `
                      <div class="flex items-center space-x-4">
                        <a href='${server.url}' target='_blank' class="text-green-500 hover:text-green-700 dark:text-green-300 dark:hover:text-green-100" title="查看">
                          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                            <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                          </svg>
                        </a>
                        <a href='/server/edit/${server.id}' class="text-blue-500 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-100" title="編輯">
                          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"></path>
                          </svg>
                        </a>
                        <button onclick="confirmDelete('${server.id}', '${server.name}')" 
                            class="flex items-center justify-between px-2 py-2 text-sm font-medium leading-5 text-purple-600 rounded-lg dark:text-gray-400 focus:outline-none focus:shadow-outline-gray hover:text-red-600" 
                            aria-label="刪除">
                            <svg class="w-5 h-5" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                              <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                            </svg>
                        </button>
                      </div>
                    `;
            row.appendChild(actionCell);
            serverTableBody.appendChild(row);
        }
    })

function deleteServer(serverId) {
    fetch(`/server/del/${serverId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(jsonData => {
        if (jsonData.success) {
            Swal.fire({
                title: '刪除成功',
                text: jsonData.message,
                icon: 'success',
                confirmButtonColor: '#059669',
                customClass: {
                    popup: 'dark:bg-gray-800 dark:text-gray-200',
                    title: 'dark:text-gray-200',
                    content: 'dark:text-gray-400'
                }
            }).then(() => {
                location.reload();
            });
        } else {
            Swal.fire({
                title: '刪除失敗',
                text: jsonData.message,
                icon: 'error',
                confirmButtonColor: '#dc2626',
                customClass: {
                    popup: 'dark:bg-gray-800 dark:text-gray-200',
                    title: 'dark:text-gray-200',
                    content: 'dark:text-gray-400'
                }
            });
        }
    })
    .catch(error => {
        console.error('刪除伺服器時發生錯誤:', error);
        Swal.fire({
            title: '網路錯誤',
            text: '請檢查網路連線並重試',
            icon: 'error',
            confirmButtonColor: '#dc2626',
            customClass: {
                popup: 'dark:bg-gray-800 dark:text-gray-200',
                title: 'dark:text-gray-200',
                content: 'dark:text-gray-400'
            }
        });
    });
}