const url = '/api/servers';
fetch(url)
    .then(response => response.json())
    .then(jsonData => {
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

        // 获取表格的tbody元素
        const serverTableBody = document.getElementById('serverTableBody');

        // 遍历服务器对象并动态生成HTML代码
        for (const serverId in jsonData.server) {
            const server = jsonData.server[serverId];

            // 创建一个新的<tr>元素
            const row = document.createElement('tr');
            row.classList.add('text-gray-700', 'dark:text-gray-400');

            // 创建<td>元素并添加内容
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
                      <a href='${server.url}'>
                        <span class="px-2 py-1 font-semibold leading-tight text-green-700 bg-green-100 rounded-full dark:bg-green-700 dark:text-green-100">
                          查看
                        </span>
                      </a>
                      <a href='/server/edit/${server.id}'>
                        <span class="px-2 py-1 font-semibold leading-tight text-gray-700 bg-gray-100 rounded-full dark:text-gray-100 dark:bg-gray-700">
                          編輯
                        </span>
                      </a>
                      <a href='/server/del/${server.id}'>
                        <span class="px-2 py-1 font-semibold leading-tight text-red-700 bg-red-100 rounded-full dark:text-red-100 dark:bg-red-700">
                          刪除
                        </span>
                      </a>
                    `;
            row.appendChild(actionCell);

            // 将新的<tr>元素添加到表格中
            serverTableBody.appendChild(row);
        }
    })