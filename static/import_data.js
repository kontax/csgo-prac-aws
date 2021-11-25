
$(function () {
    $('#table').bootstrapTable({data: []});
    setButtonVisibility();
    $('#mapSelect').on('change', setButtonVisibility);
    var intervalID = window.setInterval(getServerStatus, 5000);
});

function getServerStatus() {
    var url = `https://csgo-api.${SERVER_HOSTNAME}/status`;
    httpGetAsync(url, formatTable);
}

function formatTable(data) {
    var $table = $('#table');
    statusData = [];
    if(data['task_details'] != null) {

        for(var taskDetails of data['task_details']) {
            var envVars = [];
            var overrides = taskDetails["overrides"]["containerOverrides"][0]["environment"];
            for(var override of overrides) {
                envVars.push(override['name'] + ': ' + override['value']);
            }

            statusData.push({
                "taskArn": taskDetails["taskArn"],
                "publicIp": taskDetails["publicIp"],
                "hostnames": taskDetails["hostnames"],
                "startedAt": taskDetails["startedAt"],
                "lastStatus": taskDetails["lastStatus"],
                "desiredStatus": taskDetails["desiredStatus"],
                "cpu": taskDetails["cpu"],
                "memory": taskDetails["memory"],
                "overrides": JSON.stringify(envVars),
                "stopCode": taskDetails["stopCode"],
                "stoppedReason": taskDetails["stoppedReason"],
                "stoppingAt": taskDetails["stoppingAt"],
                "stoppedAt": taskDetails["stoppedAt"],
                "stopServer": taskDetails["taskArn"],
            });
        }
    }
    console.log("Updating table with new data");
    $('#table').bootstrapTable('load', statusData);
}

function setButtonVisibility() {
    var mapChoice = $('#startServerParams')
        .serializeArray()
        .filter(m => m["name"] == "MAP")[0]
        .value;
    var btn = $('#startServerButton');
    btn.prop('disabled', (mapChoice == "Choose Map..."));
}

function updateServer() {
    var url = `https://csgo-api.${SERVER_HOSTNAME}/start`
    httpPostAsync(url, [], getServerStatus);
}

function startServer() {
    var form = $('#startServerParams');
    var data = form.serializeArray();
    var url = `https://csgo-api.${SERVER_HOSTNAME}/start`;
    console.log(data);
    httpPostAsync(url, data, getServerStatus);
}

function stopServer(task_arn) {
    var serverData = { "task_arn": task_arn };
    var url = `https://csgo-api.${SERVER_HOSTNAME}/stop`;
    httpPostAsync(url, serverData, getServerStatus);
}

function StopFormatter(value, row, index) {
  return `
    <button type="submit" class="btn btn-primary" onclick="stopServer('${value}')">Stop</button>
  `;
}

function LinkFormatter(value, row, index) {
  return `
    <a href=steam://connect/${value}:27015/${SERVER_PASSWORD}>${value}</a>
  `;
}

function httpPostAsync(theUrl, data, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.responseType = 'json';
    console.log(theUrl);
    console.log(data);
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.response);
    }
    xmlHttp.open("POST", theUrl, true); // true for asynchronous 
    xmlHttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xmlHttp.send(JSON.stringify(data));
}

function httpGetAsync(theUrl, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.responseType = 'json';
    console.log(theUrl);
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.response);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}

