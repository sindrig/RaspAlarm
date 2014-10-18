$(function(){
    $('button').on('click', process_request);
    $('#dialog').dialog({
        autoOpen: false
    });
});

var process_request = function(evt){
    evt.preventDefault()
    switch($(this).attr('id')){
        case 'startstream':
            start_stream();
            break;
        case 'stopstream':
            stop_stream();
            break;
        case 'download_videos':
            stop_stream();
            download_videos();
            break;
        default:
            alert('Not implemented!');
            break;
    }
}

STREAMING = false;
STREAM_NUM_IMAGE = 0;

var start_stream = function(){
    var data = $('.control select, .control input').map(function(){
        return {'name': $(this).attr('name'), 'value': $(this).val()}
    });
    $.ajax('/start_streaming', {
        data: data,
        success: function(data){
            if(data.success){
                STREAMING = true;
                get_image();
             }else{
                 alert(data.error);
             }
        }
    });
};

var get_image = function(){
    if(STREAMING){
        var thisnum = STREAM_NUM_IMAGE++;
        var url = '/get_stream_image?_='+(thisnum);
        var img = $('<img>')
            .css('zIndex', '-1')
            .css('position', 'absolute')
            .attr('src', url);
        img.one('load', function(){
            $(this).css('zIndex', thisnum);
            $('.old').remove();
            get_image();
        }).each(function(){
            if(this.complete){
                $(this).load();
            }
        });
        var stream = $('.stream');
        stream.find('img').addClass('old');
        img.appendTo(stream);
    }
};

var stop_stream = function(){
    STREAMING = false;
    $.ajax('/stop_streaming', {
        success: function(data){
            if(!data.success){
                alert('Error!');
                alert(data);
            }
        }
    });
};

var download_videos = function(){
    $('#dialog').load('/download_videos').dialog('open');
};
