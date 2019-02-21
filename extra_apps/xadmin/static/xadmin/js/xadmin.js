$('#id_mypage').change(function () {
        var module = $('#id_mypage').find('option:selected').val(); //获取父级选中值
        $('#id_myalbum')[0].selectize.clearOptions();// 清空子级
        $.ajax({
            type: 'get',
            url: '/select/mypage_myalbum/?module=' + module,
            data: '',
            async: true,
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader('X-CSRFToken', '{{ csrf_token }}')
            },
            success: function (data) {

                data = JSON.parse(data.album)//将JSON转换
                console.log(data);
                for (var i = 0; i < data.length; i++) {

                    var test = {text: data[i].fields.name, value: data[i].pk, $order: i + 1}; //遍历数据,拼凑出selectize需要的格式
                    console.log(test);
                    $('#id_myalbum')[0].selectize.addOption(test); //添加数据
                }
            },
            error: function (xhr, textStatus) {
                console.log('error')
            }
        })
    })
