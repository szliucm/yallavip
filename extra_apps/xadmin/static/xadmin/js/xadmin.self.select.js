(function($){
　　function linkage_query(){
　　　　$("#select1_id").change(function(){
　　　　　　var val = $(this).val();
        　　url = "联动查询的url加上参数";
　　　　　　getSecNav(url, select2_id);
　　　　});
           　　　　
　　function getSecNav(url, id){
　　　　　　$.ajax({
　　　　　　　　type:"GET",
　　　　　　　　url:url,
　　　　　　　　async:true,
　　　　　　　　beforeSend:function(xhr){
　　　　　　　　　　xhr.setRequestHeader("X-CSRFToken", $.getCookie("csrftoken"))
　　　　　　　　},
　　　　　　　　success:function(data){
　　　　　　　　　　$("#id")[0].selectize.clearOptions();
            　　　　for(var i=0;i<data.length;i++){
　　　　　　　　　　　　$("#id")[0].selectize.addOption({"text":data[i].name, value:data[i].id, $order:i+1})
　　　　　　　　　　}
　　　　　　　　},
　　　　　　　　error:function(xhr, textStatus){
　　　　　　　　　　console.log(xhr);
            　　　　console.log(testStatus)
　　　　　　　　}
　　　　　　});
　　　　}
　　}
　　linkage_query();
})(jQuery);