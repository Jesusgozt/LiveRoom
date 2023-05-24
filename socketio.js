document.addEventListener('DOMContentLoaded', () => {
    var socket = io.connect();

    let hosttrack;
    let isplaying;
    let trackuri;
    joinRoom(room);

    socket.on('message', data => {
        const p = document.createElement('p');
        const br = document.createElement('br');
        p.innerHTML = data.username + ': ' + data.msg + ' ' + data.time_stamp;
        document.querySelector('#chat').append(p);

    });


    socket.on('some event', data => {
        const p = document.createElement('p');
        hosttrack = data['tracktime'];
        isplaying = data['isplaying'];
        trackuri = data['trackuri'];
        p.innerHTML = data.tracktime + ': ' + ' ' + data.trackuri;
        document.querySelector('#chat').append(p);

    });

    //Send message
    document.querySelector('#btnSendMessage').onclick = () => {
        socket.send({ 'msg': document.querySelector('#fmessage').value, 'username': username, 'room': room });

    };

    document.querySelector('#btnSync').onclick = () => {

        socket.emit('my event', { 'tracktime': hosttrack, 'trackuri': trackuri, 'isplaying': isplaying, 'room': room });

    };

    document.querySelector('#btnStart').onclick = () => {

        socket.emit('start thread', { 'room': room });

    };

    function leaveRoom(room) {
        socket.emit('leave', { 'username': username, 'room': room });

    }

    function joinRoom(room) {
        socket.emit('join', { 'username': username, 'room': room });

        document.querySelector('#chat').innerHTML = ''

    }

})
