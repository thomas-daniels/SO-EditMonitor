function escape(unescaped) {
    return unescaped.replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;");
}

function process(msg) {
    var qlMatch = /^\[[0-9: -]+\] Queue length: (\d+)$/i.exec(msg);
    if (qlMatch !== null && qlMatch !== undefined) {
        document.getElementById("queueLengthCell").innerHTML = qlMatch[1];
        return;
    }

    var quotaMatch = /^\[[0-9: -]+\] API quota: (\d+)$/i.exec(msg);
    if (quotaMatch !== null && quotaMatch !== undefined) {
        document.getElementById("quotaCell").innerHTML = quotaMatch[1];
        return;
    }

    var reportsTable = document.getElementById("reportsTable");
    var newRow = reportsTable.insertRow(1);
    var dateCell = newRow.insertCell(0);
    var contentCell = newRow.insertCell(1);
    dateCell.innerHTML = /^\[([0-9 :-]+)\]/.exec(msg)[1];
    msg = msg.replace(/^\[[0-9 :-]+\]/, "").trim();
    contentCell.innerHTML = msg.replace(/\[([0-9]+)\]\(([^)]+)\)/, "<a href='$2'>$1</a>");
}

window.onload = function () {
    var verboseOutput = "";
    var smallerOutput = "";
    var showVerbose = false;

    var hostname = window.location.hostname;
    hostname = hostname == "" ? "localhost" : hostname;
    var ws = new WebSocket("ws://" + hostname + ":4001/");
    ws.onmessage = function (msg) {
        var logElem = document.getElementById("log");

        var data = msg.data;
        var verbose = data[0] == "-";
        var message = data.substring(1);
        process(message);
        verboseOutput = message + "<br>" + verboseOutput;
        if (!verbose) {
            smallerOutput = message + "<br>" + smallerOutput;
        }

        if (showVerbose) {
            logElem.innerHTML = verboseOutput;
        } else {
            logElem.innerHTML = smallerOutput;
        }
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