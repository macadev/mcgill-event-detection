var video = videojs("my-video");
var playing;
var initialX, initialY;
var iX, iY, pX, pY;
var time, url, email;
var data;

function offset(type){
    var offset = $("#my-video").offset();

    if (type == "top") {
        return offset.top;
    } else if (type == "left") {
        return offset.left;
    } else {
        return "";
    }
}

function updateURL(){
    url = $("#url").val();
    video.src(url);
}

function submit(){
    email = $("#email").val();
    url = $("#url").val();
    sendData(email, url, time);
}

function ROI(e) {
    $(".video-js").css("pointer-events", "none");
    $(document).bind("mousedown", startSelect);
    playing = !video.paused();
    if(playing){
        video.pause();
    }
}

function startSelect(e) {
    $(document).unbind("mousedown", startSelect);
    $(".ghost-select").addClass("ghost-active");
    $(".ghost-select").css({
        'left': e.pageX,
        'top': e.pageY
    });

    initialX = e.pageX;
    initialY = e.pageY;

    $(document).bind("mouseup", endSelect);
    $(document).bind("mousemove", openSelector);

    iX = initialX - offset("left");
    iY = initialY - offset("top");
    pX = iX;
    pY = iY;

    printData();
}

function endSelect(e) {
    $(document).unbind("mousemove", openSelector);
    $(document).unbind("mouseup", endSelect);
    $(".ghost-select").removeClass("ghost-active");
    $(".ghost-select").width(0).height(0);
    $(".video-js").css("pointer-events", "auto");
    time = video.currentTime();
    $("#time").html("Time: " + time);
    if(playing){
        video.play();
    }
}

function openSelector(e) {
    var w = Math.abs(initialX - e.pageX);
    var h = Math.abs(initialY - e.pageY);

    $(".ghost-select").css({
        'width': w,
        'height': h
    });
    if (e.pageX <= initialX && e.pageY >= initialY) {
        $(".ghost-select").css({
            'left': e.pageX
        });
    } else if (e.pageY <= initialY && e.pageX >= initialX) {
        $(".ghost-select").css({
            'top': e.pageY
        });
    } else if (e.pageY < initialY && e.pageX < initialX) {
        $(".ghost-select").css({
            'left': e.pageX,
            "top": e.pageY
        });
    }

    pX = e.pageX - offset("left");
    pY = e.pageY - offset("top");
    iX = initialX - offset("left");
    iY = initialY - offset("top");

    printData();
}

function printData(){
    $("#topLeft").html("TL: " + iX + ", " + iY);
    $("#topRight").html("TR: " + pX + ", " + iY);
    $("#bottomRight").html("BR: " + pX + ", " + pY);
    $("#bottomLeft").html("BL: " + iX + ", " + pY);
}

function sendData(email, url, time){
    var data2 = {'URL' : url, 'TL' : iX + ", " + iY, 'TR' : pX + ", " + iY, 'BR' : pX + ", " + pY, 'BL' : iX + ", " + pY, 'Time' : iX + ", " + iY, 'Email' : email};
    // hard coding for now
    var valTL = iX + ", " + iY;
    var valTR = pX + ", " + iY;
    var valBR = pX + ", " + pY;
    var valBL = iX + ", " + pY;

    data = '{"user_email":"' + email + '", "youtube_url":"' + url + '", "TL":"' + valTL + '", "TR":"' + valTR + '", "BR":"' + valBR + '", "BL":"' + valBL + '", "time":"' + time + '"}';
    console.log("sending data!");
    console.log(data);

    $.ajax({
        url: '/predict',
        type: 'POST',
        dataType: 'json',
        contentType: "application/json",
        success: function (data) {
            console.log(data);
        },
        headers: {'Content-Type':'application/json'},
        processData: false,
        data: data
    }); 
}
