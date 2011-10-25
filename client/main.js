/**
 * snake by Karshan Sharma <sharma34@illinois.edu>
 * simple html5 implementation of the classic snake game
 */

var FPS = 60;
var server = "localhost:1337";
var ctx;

var width, height;

function print(m) {

    var screen = document.getElementById("screen");
    if (screen !== null && screen !== undefined) {
        screen.innerHTML += m;
        screen.scrollTop = screen.scrollHeight;
    }

}

function println(m) {
    print(m + '\n');
}

var my_id = -1;
var snakes_flip = null;
var snakes = null;
var game = null;
var socket;
var connected = false;

function init()
{
    var canvas = document.getElementById('canvas');
    document.onkeydown = key_handler;

    if (!canvas.getContext) {
        alert("Sorry your browser doesn't support the canvas element");
        return;
    }

    if (!("WebSocket" in window)) {
        alert("Sorry your browser doesn't support WebSockets");
    }


    try {
        socket = new WebSocket("ws://" + server + "/snake_server");
    } catch(exception) {
        alert("Exception while creating WebSocket: " + exception);
    }

    socket.onopen = function() {
        println("socket - onopen: readyState " + socket.readyState);
        connected = true;

        try {
            socket.send("connect");
        } catch(e) {
            alert("send connect failed: " + e);
        }
    }

    socket.onmessage = function(msg) {
//        println("socket - recvd: " + msg.data);

        obj = JSON.parse(msg.data);
        if (obj.your_id !== null && obj.your_id !== undefined)
            my_id = obj.your_id;
        if (snakes_flip === null && snakes !== null)
            snakes_flip = snakes_copy(snakes);
        snakes = obj.game.snakes;
        game = obj.game;
        draw();
    }

    socket.onclose = function() {
        println("socket  - onclose: readyState " + socket.readyState);
    }

    width = canvas.width;
    height = canvas.height;

    ctx = canvas.getContext("2d");

//    setInterval(draw, 1000/FPS);
}

function move_by_dir(p, d) {
    return { "x" : p.x + d.dx, "y" : p.y + d.dy };
}

function char_to_dir(c) {
    var dx = 0;
    var dy = 0;
    if (c == 'r')
        dx = 1;
    else if (c == 'l')
        dx = -1;
    else if (c == 'u')
        dy = -1;
    else if (c == 'd')
        dy = 1;
    return { "dx" : dx, "dy" : dy };
}

function for_each_point_on_snake(s, f) {
    head = { "x" : s.head.x, "y" : s.head.y };
    f(head);
    for (var i = 0; i < s.tail.length; i++) {
        head = move_by_dir(head, char_to_dir(s.tail[i]));
        f(head);
    }
    return head;
}

function draw() {
    x_r = width/game.width;
    y_r = width/game.width;
    if (my_id != -1) {
        /*if (snakes_flip !== null) {
            ctx.fillStyle = "rgb(200, 0, 0)";
            for (var i = 0; i < snakes_flip.length; i++) {
                var s = snakes_flip[i];
                for_each_point_on_snake(s, function(p) {
                    ctx.clearRect(p.x * x_r, p.y * y_r, x_r, y_r);
                });
            }
            snakes_flip = null;
        }*/
        ctx.clearRect(0, 0, width, height);
        for (var i = 0; i < snakes.length; i++) {
            var s = snakes[i];
            if (s.status === "alive") {
                println("drawing: (" + s.head.x + ", " + s.head.y + ")" + "->" + s.tail);
                if (s.id == my_id) {
                    ctx.fillStyle = "rgb(200, 0, 0)";
                } else {
                    ctx.fillStyle = "rgb(0, 0, 200)";
                }
                for_each_point_on_snake(s, function(p) {
                    ctx.fillRect(p.x * x_r, p.y * y_r, x_r, y_r);
                });
            }
        }
        ctx.fillStyle = "rgb(0, 0, 0)";
        ctx.fillRect(game.fruit.x * x_r, game.fruit.y * y_r, x_r, y_r);
    }
}

function snakes_copy(src) {
    var ret = [];
    for (var i = 0; i < src.length; i++) {
        var s = src[i];
        var obj = {};
        obj.status = s.status;
        obj.id = s.id;
        obj.x = s.x;
        obj.y = s.y;
        obj.dx = s.dx;
        obj.dy = s.dy;
        ret.push(obj);
    }
    return ret;
}

function key_handler(event) {
    var keyCode;

    event = event || window.event;
    keyCode = event.keyCode;

    var dx = 0; var dy = 0;
    if (keyCode == 37) { // left
        dx = -1; dy = 0;
    } else if (keyCode == 38) { // up
        dx = 0; dy = -1;
    } else if (keyCode == 39) { // right
        dx = 1; dy = 0;
    } else if (keyCode == 40) { // down
        dx = 0; dy = 1;
    }

    if ((dx != 0 || dy != 0) && connected) {
        try {
            socket.send('{ "dx" : ' + dx + ', "dy" : ' + dy + '}');
        } catch(e) {
            alert("send failed: " + e);
        }
    }
}
