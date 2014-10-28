$(function(){
    $('button').on('click', process_request);
    $('#dialog').dialog({
        autoOpen: false,
        title: 'Videos available for download',
        // position: ['center',20],
        width: '500',
        height: '400'
    });
    $('.update-ui').on('click', function(){
        update_ui(true);
    })
    update_ui();
});

var update_ui = function(no_timeout_call){
    no_timeout_call = no_timeout_call || false;
    if(!STREAMING){
        $('button').not('#download_videos').attr('disabled', 'disabled');
        $.ajax('/status', {
            success: function(data){
                if(data.streaming){
                    $('#stopstream').attr('disabled', null);
                    if(!STREAMING){
                        STREAMING = true;
                        get_image();
                    }
                }else if(data.armed){
                    $('#disarm').attr('disabled', null);
                }else{
                    $('#startstream, #arm').attr('disabled', null);
                }
                $('.temperature span').text(data.temp);
                if(!no_timeout_call){
                    setTimeout(update_ui, 60*1000);
                }
            }
        });
    }else{
        if(!no_timeout_call){
            setTimeout(update_ui, 60*1000);
        }
    }
};

var process_request = function(evt){
    STREAMING = false;
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
        case 'arm':
            arm();
            break;
        case 'disarm':
            disarm();
            break;
        default:
            alert('Not implemented!');
            break;
    }
    update_ui(true);
};

STREAMING = false;
STREAM_NUM_IMAGE = 0;

var start_stream = function(){
    var data = $('.control select, .control input').map(function(){
        if($(this).is('[type="radio"]') && !$(this).is(':checked')){
            return null;
        }
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
        img.on('error', function(){
            STREAMING = false;
            update_ui(true);
        }).one('load', function(){
            $(this).css('zIndex', thisnum % 500);
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
    $.ajax('/stop_streaming', {
        success: function(data){
            if(!data.success){
                alert('Error!');
                alert(data);
            }
        }
    });
};

var arm = function(){
    $.ajax('/arm_motion', {
        success: function(data){
            if(!data.success){
                alert('Error!');
                alert(data);
            }
        }
    });
};

var disarm = function(){
    $.ajax('/disarm_motion', {
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
