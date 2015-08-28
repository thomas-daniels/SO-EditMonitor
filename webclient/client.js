function process(msg, data) {
    var isVerbose = msg[0] === "-";
    msg = msg.substring(1);
    data.verboseLog.unshift(msg);
    if (!isVerbose) data.smallerLog.unshift(msg);

    var qlMatch = /^\[[0-9: -]+\] Queue length: (\d+)$/i.exec(msg);
    if (qlMatch !== null && qlMatch !== undefined) {
        data.queue = parseInt(qlMatch[1], 10);
        return data;
    }

    var quotaMatch = /^\[[0-9: -]+\] API quota: (\d+)$/i.exec(msg);
    if (quotaMatch !== null && quotaMatch !== undefined) {
        data.quota = parseInt(quotaMatch[1], 10);
        return data;
    }

    var report = { date: "", content: "" }
    report.date = /^\[([0-9 :-]+)\]/.exec(msg)[1];
    msg = msg.replace(/^\[[0-9 :-]+\]/, "").trim();
    report.content = msg.replace(/\[([0-9]+)\]\(([^)]+)\)/, "<a href='$2'>$1</a>");
    data.reports.push(report);
    return data;
}

var verboseOutput = "";
var smallerOutput = "";
var showVerbose = false;

function updateDom(newQueueLength, newQuota, newReports, newVerboseLogData, newShorterLogData) {
    if (newQueueLength !== -1) document.getElementById("queueLengthCell").innerHTML = newQueueLength.toString();
    if (newQuota !== -1) document.getElementById("quotaCell").innerHTML = newQuota.toString();
    if (newReports !== null && typeof (newReports) !== "undefined" && newReports.length > 0) {
        var reportsTable = document.getElementById("reportsTable");
        for (var i = 0; i < newReports.length; i++) {
            var report = newReports[i];
            var newRow = reportsTable.insertRow(1);
            var dateCell = newRow.insertCell(0);
            var contentCell = newRow.insertCell(1);
            dateCell.innerHTML = report.date;
            contentCell.innerHTML = report.content;
        }
    }
    if (newVerboseLogData !== null && typeof (newVerboseLogData) !== "undefined" && newVerboseLogData.length > 0) {
        verboseOutput = newVerboseLogData.concat([verboseOutput]).join("<br>");
    }
    if (newShorterLogData !== null && typeof (newShorterLogData) !== "undefined" && newShorterLogData.length > 0) {
        smallerOutput = newShorterLogData.concat([smallerOutput]).join("<br>");
    }
    var logElem = document.getElementById("log");
    if (showVerbose) logElem.innerHTML = verboseOutput;
    else logElem.innerHTML = smallerOutput;
}

window.onload = function () {
    document.getElementById("verboseChk").checked = false;
    var hostname = window.location.hostname;
    hostname = hostname === "" ? "localhost" : hostname;
    var isPayload = false;
    var ws = new WebSocket("ws://" + hostname + ":4001/");
    var data = { queue: -1, quota: -1, reports: [], verboseLog: [], smallerLog: [] };
    ws.onmessage = function (msg) {
        var message = msg.data;
        if (message === "payload-start") {
            isPayload = true;
            return;
        } else if (message === "payload-end") {
            isPayload = false;
            updateDom(data.queue, data.quota, data.reports, data.verboseLog, data.smallerLog);
            data = { queue: -1, quota: -1, reports: [], verboseLog: [], smallerLog: [] };
            return;
        }
 
        data = process(message, data);
        if (!isPayload) updateDom(data.queue, data.quota, data.reports, data.verboseLog, data.smallerLog);
    };

    ws.onclose = function () {
        document.getElementById("error").innerHTML = "Warning! Web socket connection closed -- try refreshing the page to restore connection.";
    }

    document.getElementById("verboseChk").onclick = function () {
        showVerbose = document.getElementById("verboseChk").checked;
        var logElem = document.getElementById("log");
        if (showVerbose) {
            logElem.innerHTML = verboseOutput;
        } else {
            logElem.innerHTML = smallerOutput;
        }
    };

    var tabheaders = document.getElementsByClassName("tabheader");
    var tabs = [];
    for (var i = 0; i < tabheaders.length; i++) {
        var curr = tabheaders[i];
        var currFor = curr.getAttribute("data-for");
        tabs.push(currFor);
        curr.onclick = function (e) {
            e = e || window.event;
            var elem = e.target || e.srcElem;
            var elemFor = elem.getAttribute("data-for");
            document.getElementById(elemFor).className = "tabpage";
            elem.className = "tabheader selected";
            for (var i = 0; i < tabheaders.length; i++) {
                var currDataFor = tabheaders[i].getAttribute('data-for');
                if (currDataFor !== elemFor) {
                    document.getElementById(currDataFor).className = "tabpage hidden";
                    tabheaders[i].className = "tabheader";
                }
            }
        };
    }
};