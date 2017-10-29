var http = require("http");
setInterval(function() {
	http.get("https://peaceful-harbor-54831.herokuapp.com");
}, 10000);

const evtSource = new EventSource("/tick");

evtSource.addEventListener(
    "tick", 
    function(e) {
        let clock = document.getElementById("clock");
        let obj = JSON.parse(e.data);        
        clock.innerHTML = obj.data;
    }, 
    false
)

