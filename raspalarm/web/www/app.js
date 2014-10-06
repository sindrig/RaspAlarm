$(function(){
    $('button').on('click', process_request);
});

var process_request = function(evt){
    evt.preventDefault()
    switch($(this).attr('id')){
        case 'startstream':
            start_stream();
            break;
    }
}

STREAMING = false;
STREAM_NUM_IMAGE = 0;

var start_stream = function(){
    $.ajax('/start_streaming', {
        success: function(data){
            if(data.success){
                STREAMING = true;
                get_image();
            }
        }
    })
};

var get_image = function(){
    if(STREAMING){
        var thisnum = STREAM_NUM_IMAGE++;
        var url = '/get_stream_image?_='+(thisnum);
        var img = $('<img>').css('zIndex', '-1').attr('src', url);
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
}
