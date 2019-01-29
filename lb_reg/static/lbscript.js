        var socket
        var t0 = 0;
        var t1 = 0;
        var interval = 0;
        var interval_timer = 0;

        $(document).ready(function() {
            var url = "http://" + document.domain + ":" + location.port;
            console.log( url);
            socket = io.connect(url + "/dd");
            console.log("connected");
            socket.emit("conn", [location.pathname.split('/').slice(-1)[0]])

            $(".reg_input").keydown(function(event){
                console.log(event.which)
                var id = $(this).attr("id")
                var form_doc = document.getElementById(id).parentElement
                if (event.which == 13) { // carrage return
                    msg = [$(this).attr("id"),$(this).val(),location.pathname.split('/').slice(-1)[0]]
                    socket.emit("memwrt", msg);
                    form_doc.reset();
                    return false
                }
                if (event.which == 27) { // escape
                    msg = [$(this).attr("id"),"",location.pathname.split('/').slice(-1)[0]]
                    socket.emit("memwrt", msg);
                    form_doc.reset();
                    return false
                }
             });

            $("#play-btn").on('click',function(event) {
                console.log($(this).attr("id"));
                $(this).blur();
                console.log($("#macrofile option:selected").val());
                if ($("#macrofile option:selected").val() == "") {
                    alert("Select a macro file");
                }
                else {
                    socket.emit("macro",["play", $("#macrofile option:selected").val(),location.pathname.split('/').slice(-1)[0]]);
                }
                return true;
            });
            $("#save-btn").on('click',function(event) {
                console.log($(this).attr("id"));
                $(this).blur();
                socket.emit("macro",["save",location.pathname.split('/').slice(-1)[0]]);
                return true;
            });
            $("#clear-btn").on('click',function(event) {
                console.log($(this).attr("id"));
                $(this).blur();
                socket.emit("macro",["clear",location.pathname.split('/').slice(-1)[0]]);
                return true;
            });
            $("#record-btn").on('click change',function(event) {
                var cur_text = $(this).text();
//                console.log(cur_text)
                if (cur_text.search("Start") < 0) {
//                    console.log("not Start match")
                    cur_text = cur_text.replace("Stop","Start");
                } else {
                    cur_text = cur_text.replace("Start","Stop");
                }
                $(this).text(cur_text)
                $(this).blur();
                socket.emit("macro",["record",location.pathname.split('/').slice(-1)[0]]);
                return false;
            });

            $('#myForm input').on('change', function() {
               var portname = ($('input[name=optradio]:checked', '#myForm').val()); 
               console.log(portname)
               socket.emit("port_select", [location.pathname.split('/').slice(-1)[0],portname])
            });

            socket.on('macro_status', function(data) {
                 var data_obj = JSON.parse(data)
                console.log(data_obj)
                $("#record-btn").text('REC ' + data_obj[0])
                $("#save-btn").text('Save (' + data_obj[1] + ')')
                update_macrofile(data_obj[2])
            });

            
            function update_macrofile(file_list) {
                var select = $("#macrofile");
                console.log(select)
                select.html('<option value="">Select</option>');
                for (file in file_list) {
                    select.append("<option value='"+file_list[file]+ "'>" +file_list[file]+ "</option>");
                }
            }
            

             
            $(".reg_input").focus(function(){
                console.log("input")
                var form_doc = document.getElementById($(this).attr("id")).parentElement
                $(this).select()
                })
                
            $(".radio-inline").focus(function(){
                console.log("radio_inline")
                console.log($(this))
                });
                
            socket.on('update_table', function(msg) {
                update_table(msg)
                upd_interval()
            });
            function update_table( data ){
                 var tbl_obj = JSON.parse(data)
                for (label in tbl_obj) {
                    document.getElementById(label).setAttribute('value',tbl_obj[label]);
                    document.getElementById(label).reg_input = tbl_obj[label];
                    
               }
            }
            socket.on('update_system', function(msg) {
                update_system(msg)
            });
           function update_system( data ){
                 var tbl_obj = JSON.parse(data);
                for (label in tbl_obj) {
                    document.getElementById(label).innerHTML = tbl_obj[label];
                    
               }
            }
            socket.on('set_portname', function(msg) {
                console.log(msg)
                $('input[name=optradio][value=' + msg + ']').prop('checked', true);
                
            });
            socket.on('portstatus', function(port_obj) {
                update_portstatus(port_obj);
                upd_interval()
            });

            function upd_interval() {
                if (interval > 0) {
                    var t1 = performance.now();
                    var diff=(t1-t0);
                    console.log("Time "+ diff + "ms");
                    console.log(interval + " " +(2*diff));
                    if (2*diff > interval) {
                        clearInterval(interval_timer)
                        interval=(2*diff);
                        console.log("new interval " + interval);
                        start_interval_timer()
                        }
                }
            };
            function update_portstatus( data ){
                 port_obj = JSON.parse(data)
                for (portn in port_obj) {
                    port = port_obj[portn]
                    for (x in port) { 
                        document.getElementById(portn+x).innerHTML = port[x];
                    }
                }
            }
            socket.on('getval', function(msg) {
                console.log("getval")
                m = msg
                console.log(m[0] + m[1]);
                x = document.getElementById(m[0]).title = m[1];
                console.log(x)
            });
            
            $(".hideclass").click(function(event) {
                console.log("hideclass")
                $('td:nth-child(4)').toggle()
                return false
            });
            $("#file").change(function() { 
                console.log($(this)); 
                console.log($(this).val())
            
            });
            
            $('#filelist').on('change', function() {
                console.log($(this)); 
                console.log($(this).val())
               /* Remove all options from the select list */
               $(this).empty();
                var my_list = ['another.json', 'andanother.json', 'evenmore.json'];
               /* Insert the new ones from the array above */
               console.log(my_list)
               for (x in my_list) {
                    console.log(x)
                   $(this).append('<option value="'+my_list[x]+'">'+my_list[x]+'</option>');
               };
            });
       });
