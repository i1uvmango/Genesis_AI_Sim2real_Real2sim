/**
 * Description : 공통함수
 * author : qkrgksgh725
 */
var cmIframeFnc = {
	name : null
	, logic : null
};

var cmFunction = {
		/**
		 * form 안에 있는 데이터의 초기화한다.
		 * @param {String} formId	form Id 기재 <form id="searchForm"..
	     * hidden 타입 초기화 해야할 경우 class 에 clear 선언
         * 그외 타입 초기화 하지 말아야할 경우 class에 no_clear 선언
         * 예시 
         * cmFunction.formClear("searchForm");
		 */
		formClear : function(formId) {
			$("#"+formId+" input").not(':button, :submit, :reset, :hidden, :checkbox, :radio, :text.no_clear').val("");
			$("#"+formId+" input:file").siblings('label').text("선택된 파일없음");
			$("#"+formId+" input:hidden.clear").val("");
			$("#"+formId+" select").not(".no_clear").find('option:first').prop('selected', 'selected');
			$("#"+formId+" textarea").not(".no_clear").val("");
		    $("#"+formId+" :checkbox, :radio").not(".no_clear").prop('checked', false);
		}
		/**
		 * submit 전송
		 * @param {String} reqUrl	요청할 URL 기재
	     * @param {Object | Array | String } object  요청할 Paramter 기재
         * @param {String} reqMethod {"post" | "get"} defualt : post
         * @param {Object | Array | String } 추가로 요청할 Parmater 기재 
         * @param {String } iframe 사용여부
         * 예시 
		 *  cmFunction.submit("/v4po_sample_s001.do", listFnc.clone ,"get", {seqIde : seqIde});
		 *	cmFunction.submit("/v4po_sample_s001.do", "searchForm","get");
		 *	cmFunction.submit("/v4po_sample_s001.do",{seqIde : seqIde}, "post");
		 *	cmFunction.submit("/v4po_sample_s001.do",[{name : "seqIde" , value : seqIde},{name : "seqIde", value : seqIde}]);
		 */ 
		, submit : function(reqUrl, object, reqMethod, addObject, target){
			if(reqMethod == "" || reqMethod == null || reqMethod == undefined){
				reqMethod = "post";
			}
			if(target == "" || target == null || target == undefined){
				target = "";
			}
			if(target == "iframeTag" && cmIframeFnc.logic != null){
				cmIframeFnc.name = target
				$("body").append("<iframe id=\"iframeTag\" name=\"iframeTag\"\></iframe>");
			}
			
			var trgObj = $("<form action=\""+reqUrl+"\" method=\""+reqMethod+"\" target=\""+target+"\" ></form>").appendTo('body')
			var inputHidden = "";
			if(object != undefined && object != null && object != ""){
				cmFunction.submitParams(object, trgObj);
			}	
			if(addObject != "" && addObject != null && addObject != undefined){
				cmFunction.submitParams(addObject, trgObj);
			} 
			trgObj.submit();
			//loginFnc.startSessionTimerDayjs();
		}
		/**
		 * Submit params 생성
	     * @param {Object | Array | String } object  요청할 Paramter 기재
		 */ 
		, submitParams : function(object, trgObj) {

			if(object.constructor == String ){
				if($("#"+object).find("input[type=file]").length > 0){
					trgObj.attr("enctype","multipart/form-data");
					$.each($("#"+object).find("input[type=file]"), function(idx, item){
						$(this).clone().appendTo(trgObj);
					});
				}
				$.each($("#"+object).serializeArray(), function(idx, item){
					var input = $("<input type=\"hidden\" name=\""+item.name+"\" />").appendTo(trgObj);
					input.val(item.value);
				});
				
			}else if(object.constructor == Object){
				$.each(object, function(idx, item){
					var input = $("<input type=\"hidden\" name=\""+idx+"\" />").appendTo(trgObj);
					input.val(item);
				});
			}else if(object.constructor == Array){
				$.each(object, function(idx, item){
					var input = $("<input type=\"hidden\" name=\""+item.name+"\" />").appendTo(trgObj);
					input.val(item.value);
				});
			}else{
				$.each($(object).serializeArray(), function(idx, item){
				var input = $("<input type=\"hidden\" name=\""+item.name+"\" />").appendTo(trgObj);
					input.val(item.value);
				});
			}
		}
		/**
		 * Ajax Submit 전송
		 * @param {String} reqUrl	요청할 URL 기재
	     * @param {Object | Array | String } object  요청할 Paramter 기재
		 * @param {Object | Array | String } successFn  요청이 성공 후 함수 실행
	     * @param {Object | Array | String } errorFn    요청이 실패 후 함수 실행 java에서 errorMsg 받아 올 경우 실행
		 */ 
		, ajaxSubmit : function(reqUrl, object, successFn, errorFn) {
			if(object.constructor == String ){
				object = $.param($("#"+object).serializeArray());
			}
			cmFunction.waiting.start();
			$.ajax({
				url : reqUrl
				, data: object
				, type: 'post'
				, dataType: 'json'
				, timeout: 100000 //10Sec
				, success:function(data) {
					if(data.errorMsg != undefined){
						if(errorFn == undefined){
							if(data.errorMsg != ""){
								msgFnc.alert(data.errorMsg);
							}else{
								cmFunction.error(status);
							}
						}
						typeof errorFn === "function" ? errorFn(data): null;
					}else{
						typeof successFn === "function" ? successFn(data): null;
					}

				}
				, error: function(xhr, status, error){
					cmFunction.error(status);
				}
			})
			.always(function(){
				cmFunction.waiting.stop();
				//loginFnc.startSessionTimerDayjs();
			});
		}
		, ajaxMultipartSubmit : function(reqUrl, object, successFn, errorFn) {
			var form = $('#'+object)[0];  	    
    		// Create an FormData object          
   			 var data = new FormData(form);  	   
			cmFunction.waiting.start();
			$.ajax({
				url : reqUrl
				, data: data
				, type: 'post'
				, enctype: 'multipart/form-data'
				, processData: false   
                , contentType: false
				, timeout: 100000 //10Sec
				, success:function(data) {
					if(data.errorMsg != undefined){
						if(errorFn == undefined){
							if(data.errorMsg != ""){
								msgFnc.alert(data.errorMsg);
							}else{
								cmFunction.error(status);
							}
						}
						typeof errorFn === "function" ? errorFn(data): null;
					}else{
						typeof successFn === "function" ? successFn(data): null;
					}

				}
				, error: function(xhr, status, error){
					cmFunction.error(status);
				}
			})
			.always(function(){
				cmFunction.waiting.stop();
				//loginFnc.startSessionTimerDayjs();
			});
		}
		/**
		 * Ajax Page 로드
         * @param {String } targetId  Page 로드 영역 ID 기재 
 		 * @param {String } object  요청할 Url 기재
	     * @param {Object | Array | String } object  요청할 Paramter 기재
		 */ 
		, ajaxLoad : function(targetId, reqUrl, object){
			if(object.constructor == String ){
				object = $.param($("#"+object).serializeArray());
			}
			cmFunction.waiting.start();

			$.post(reqUrl, object, function(response, status, xhr){
				if(status == "error"){
					cmFunction.error(xhr.status);
				}else{
					if(xhr.status != "200"){
						cmFunction.error(xhr.status);
					}else{
						$("#"+targetId).html(response);
					}
				}
				cmFunction.waiting.stop();
				//loginFnc.startSessionTimerDayjs();
		    });
		}
		, error : function(exCode){
			msgFnc.alert(cmMsg.error.def);
		}

		, popup : {
			open : function(popId, popNm, url, options, fullYn){
				if($("#"+popId).length < 1){
					var popParam = {
						popId : ""
						,popNm : ""
						,cbFnc : ""
					};
					popParam = options.params;
					if(popParam.constructor == Object){
						popParam.popId = popId;
						popParam.popNm = popNm;
						popParam.cbFnc = options.cbFnc || "";
					}else {
						popParam.push({name : "popId" , value : popId});
						popParam.push({name : "popNm" , value : popNm});
						popParam.push({name : "cbFnc" , value : options.cbFnc || ""});
					}
					
					var addClass = "";
					if(fullYn == "Y"){
						addClass = "full";
					}

					$("body").append("<article id=\""+popId+"\" class=\"popup "+addClass+"\" style=\"width:"+options.width+"px;height:"+options.height+"px;\"></article>");

					cmFunction.ajaxLoad(popId, url, popParam);
				}
			}
			, close : function(popId){
				$("#"+popId).remove();
				$("#mask").remove();
			}
		}
		,datePicker : function(){
			$('.datePicker').datetimepicker({
				timepicker : false
				,format : 'Y-m-d'
				,yearStart : '1900'
			});

			$('.datePicker').parent("em").next("span.ico").click(function(){
				$(this).prev("em").children("input.datePicker").datetimepicker('show');
			});
		}
		,datePickerRange : function(startId, endId){
			$('#'+startId ).datepicker( "destroy" );
			$('#'+endId ).datepicker( "destroy" );
			$('#'+startId).datepicker({
				dateFormat: "yy-mm-dd"
				, beforeShow : function(){
					var maxDate = $('#'+endId).val() ? new Date($('#'+endId).val()):null;
					$( '#'+startId ).datepicker( "option", "maxDate", maxDate );
				}
			}).on('change', function(ev){
		        var maxDate = $('#'+endId).val() != ""?$('#'+endId).val().replaceAll("-",""):"";

				if(maxDate != ""){
					if( $('#'+startId).val().replaceAll("-","") >  maxDate){
						$('#'+startId).val("");
					}
				}
		    });
			
			$('#'+endId).datepicker({
				dateFormat: "yy-mm-dd"
				, beforeShow : function(){
					var minDate = $('#'+startId).val()? new Date($('#'+startId).val()):null;
					$( '#'+endId ).datepicker( "option", "minDate", minDate );
				}
			}).on('change', function(ev){
		       var minDate = $('#'+startId).val() != "" ?$('#'+startId).val().replaceAll("-",""):"";

				if(minDate != ""){
					if( $('#'+endId).val().replaceAll("-","") <  minDate){
						$('#'+endId).val("");
					}
				}
		    });
			
			$.datepicker.setDefaults({
				monthNamesShort: ['01','02','03','04','05','06','07','08','09','10','11','12'],
				dayNamesMin: ['일','월','화','수','목','금','토'],
				showMonthAfterYear: true,
				changeYear: true,
				changeMonth: true,
			});
			
			
			
		}
		, waiting : {
			start : function(){
				$("body").append("<div class=\"loading\"><ul class=\"spinner\"><li></li><li></li><li></li><li></li></ul></div>");
			}
			, stop : function(){
				$(".loading").remove();
			}
		}
		, todate : function(){
			var today = new Date();
			var dd = today.getDate();
			var mm = today.getMonth()+1; //January is 0!
			var yyyy = today.getFullYear();

			if(dd<10) {
			    dd='0'+dd
			}

			if(mm<10) {
			    mm='0'+mm
			}

			return dd+'/'+mm+'/'+yyyy;
		}
		, lpad : function(str, padLen, padStr) {
		    if (padStr.length > padLen) {
		        return str;
		    }
		    str += ""; // 문자로
		    padStr += ""; // 문자로
		    while (str.length < padLen){
		    	str = padStr + str;
		    }
		    str = str.length >= padLen ? str.substring(0, padLen) : str;
		    return str;
		}
		, checkAll : function(targetNm){
			var chk = $("#"+targetNm+"All").is(":checked");

            if(chk){
            	$("input[name="+targetNm+"]").prop("checked", true);
			}else {
				$("input[name="+targetNm+"]").prop("checked", false);
			}
		}
		, check : function(targetNm){
			var checkCount = $("input[name='"+targetNm+"']").length;
			if($("input[name='"+targetNm+"']:checked").length == checkCount){
				$("#"+targetNm+"All").prop("checked",true);
			}else{
				$("#"+targetNm+"All").prop("checked",false);
			}
		}
		/**
		 * 문자열 데이터의 길이(length)를 반환한다.
		 * @param {String} value		값
		 * @param {"char" | "utf8" | "ascii"} unit? 단위
		 * [char] : 문자의 길이
		 * [utf8] : utf8 기준의 문자 byte size
		 * [ascii] : ascii 기준의 문자 byte size.
		 * @return {Number} 문자열 길이
		 */
		, getLength: function(value, unit) {
			if (!unit) unit = "char";
	
			var length = 0;
			switch (unit) {
				case "utf8": {
					//				for(var i = 0, c; c = value.charAt(i++); length += (c >> 11 ? 3 : c >> 7 ? 2 : 1));
					for (var i = 0, len = value.length; i < len; i++) {
						if (escape(value.charAt(i)).length >= 4)
							length += 3;
						else if (escape(value.charAt(i)) == "%A7")
							length += 3;
						else if (escape(value.charAt(i)) != "%0D")
							length++;
						else length++;
					}
					break;
				}
				case "ascii": {
					for (var i = 0, c; c = value.charAt(i++); length += c >> 7 ? 2 : 1);
					break;
				}
				default: {
					length = value.length;
				}
			}
	
			return length;
		}
		, getByteString : function(value, max){
			var length = 0;
			for (var i = 0, len = value.length; i < len; i++) {
				if (escape(value.charAt(i)).length >= 4)
					length += 3;
				else if (escape(value.charAt(i)) == "%A7")
					length += 3;
				else if (escape(value.charAt(i)) != "%0D")
					length++;
				else length++;
				
				if (length > max) return value.substring(0,i);
			}
			return value;
		}
		, getByteLength : function(value, max){
			var length = 0;
			var cnt = 0;
			for (var i = 0, len = value.length; i < len; i++) {
				if (escape(value.charAt(i)).length >= 4)
					length += 3;
				else if (escape(value.charAt(i)) == "%A7")
					length += 3;
				else if (escape(value.charAt(i)) != "%0D")
					length++;
				else length++;
				
				if (length > max) return i;
			}
			return cnt;
		}
		, copyUrl : function(obj, otherUrl){
			var url = location.origin + location.pathname;
			if(otherUrl != "" && otherUrl != null && otherUrl != undefined){
				url = otherUrl;
			}
			var param = "";
			var cnt = 0;
			$.each(obj, function(n, v){
				if(cnt == 0){
					param += "?";
				}else{
					param += "&";
				}
				param += n + "=" + v;
				cnt++;
			});
			
			if(param != ""){
				url = url + param;
			}

			var textarea = document.createElement("textarea");
		 	document.body.appendChild(textarea);
		  	textarea.value = url;
		  	textarea.select();
		  	document.execCommand("copy");
		  	document.body.removeChild(textarea);
			msgFnc.alert(cmMsg.alt.copyUrl);
		}
		, copyToClipboard : function (val) {
			var t = document.createElement("textarea");
			document.body.appendChild(t);
			t.value = val;
			t.select();
			document.execCommand('copy');
			document.body.removeChild(t);
		}
		, getParams : function(){
			var pairs = window.location.search.substring(1).split("&"),
			    params =[],
			    obj = {},
			    pair,
			    i;
			
			for ( i in pairs ) {
				if ( pairs[i] === "" ) continue;
				pair = pairs[i].split("=");
				obj = {name : decodeURIComponent( pair[0] ) , value : decodeURIComponent( pair[1] )}
				params.push(obj);
			}
			return params;
		}
		, isBlank(value){
			if(value != "" && value != null && value != undefined){
				return false;
			}
			return true;
		}
		, isNumber(value){
			return !isNaN(parseFloat(value)) && isFinite(value);
		}	
		
//		2024-09-04 모바일 체크 추가 writing by yhkim
		,_isMobile: function (){
			var browserCheckText=['iPhone','iPod','BlackBerry','Android','Windows CE','LG','MOT','SAMSUNG','SonyEricsson'];
			for (var word in browserCheckText){
				if (navigator.userAgent.toUpperCase().match(browserCheckText[word].toUpperCase()) != null){
					return true;
					break;
				}
			}
			return false;
		}
			
};


/**
 * Description : 공통메시지
 * author : qkrgksgh725
 */
var cmMsg = {
    title : "V-world 디지털트윈국토"
	, cfm : {
	　　reg : "등록하시겠습니까?"
	　　, upd : "수정하시겠습니까?"
	　　, del : "삭제하시겠습니까?"
	　　, save : "저장하시겠습니까?"
	　　, cancel_list : "취소 후 목록으로 이동하시겠습니까?"
		, secretSave : "게시글 작성시 주민등록번호, 연락처 등 개인정보가 포함되지 않았는지 확인하셨습니까?"

	}
	, alt : {
		title : "안내"
	　　, confirm : "확인"
	  ,cancel : "취소"
	　　, reg : "등록되었습니다."
	　　, upd : "수정되었습니다."
	　　, del : "삭제되었습니다."
	　　, save : "저장되었습니다."
	  , copyUrl : "URL이 복사되었습니다."
      , searchInput : "검색어를 입력하세요" 
	}
	, error : {
		def : "처리 중, 오류가 발생하였습니다."
	}
	, valid : {
		required_text : "필수 입력 항목입니다."
	　　, groupRequired_text : "최소 1개 이상 필수 입력 항목입니다."
	　　, required_check : "필수 체크 항목입니다."
	　　, required_radio : " 선택하여 주십시오."
	　　, required_select : "필수 선택 항목입니다."
	　　, required_upload : "필수 업로드 항목입니다."
	　　, phone : "전화번호 형식이 아닙니다."
	　　, email : "이메일 형식이 아닙니다."
	　　, integer : "숫자만 입력 가능합니다."
	　　, id : "ID는 6자에서 18자 사이의 영숫자 또는 숫자 여야합니다."
	  ,pwd : "띄어쓰기 없는 영문 대소문자, 특수문자(!@#$%*..), 숫자 8~18자 사용 가능합니다."
 	  ,nick : "띄어쓰기 없는 한글, 영문 대소문자, 숫자조합 2~8자 사용 가능합니다."    
	　　, number : "숫자 형식이 아닙니다."
	　　, url : "URL 형식이 아닙니다."
	　　, equals : "입력값이 일치하지 않습니다."
	　　, min : "최소"
	　　, max : "최대"
	　　, minSize : "자 이상이어야 합니다."
	　　, maxSize : "자를 초과할 수 없습니다."
	　　, maxByteSize1 : "최대 한글"
	　　, maxByteSize2 : "자리(영문"
	　　, maxByteSize3 : "자리) 이하로 입력하세요."
	　　, minValue : "최소값은"
	　　, maxValue : "최대값은"
	　　, minValue2 : "이상이어야 합니다."
	　　, maxValue2 : "이하여야 합니다."
	　　, minCheckbox1 : "최소"
	　　, maxCheckbox1 : "최대"
	　　, minCheckbox2 : "개 이상 선택하셔야 합니다."
	　　, maxCheckbox2 : "개를 초과 선택하실 수 없습니다."
	　　, onlyNumber : "숫자만 입력 가능합니다."
	　　, onlyLetter : "문자만 입력 가능합니다."
	　　, onlyLetterNumber : "문자 또는 숫자만 입력 가능합니다."
	  , onlyLetterCommaNumber : "영문자(대/소), 숫자, 콤마(.)만 입력 가능합니다." 
	　　, date : "일자 형식이 아닙니다."
	　　, dateRange : "시작일은 종료일 이후 일 수 없습니다."
	   , dateRange2 : "시작일시는 종료일시 이후로 설정할수 없습니다."
	　　, decimal : "정수 10자리 및 소수 2자리까지 허용합니다."
       , decimalRt : "정수 3자리 및 소수 2자리까지 허용합니다."
       , file_valid_false : "등록할 수 없는 파일입니다."
       , select_use : "선택한 대상이 없습니다."
       , caseRequiredInput : " 입력 시, "
       , caseRequiredSelect : " 선택 시, "
       , caseRequiredCheck : " 체크 시, "
	}
};

/**
 * Description : 공통 정규식
 * author : qkrgksgh725
 */
var cmRegex = {
	int : /^[0-9]*$/
	, phone : /^([\+][0-9]{1,3}[\ \.\-])?([\(]{1}[0-9]{2,6}[\)])?([0-9\ \.\-\/]{3,20})((x|ext|extension)[\ ]?[0-9]{1,4})?$/
	, email : /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/
	, integer : /^[\-\+]?\d+$/
	, number : /^[\-\+]?((([0-9]{1,3})([,][0-9]{3})*)|([0-9]+))?([\.]([0-9]+))?$/
	, onlyNumber : /^[0-9\ ]+$/
	, onlyLetter : /^[a-zA-Z\ \'ㄱ-ㅎ|ㅏ-ㅣ|가-힣]+$/
	, onlyLetterNumber : /^[0-9a-zA-Z]+$/
	, url : /^(https?|ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(\#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i
	//, date : /^(\d{4})[\/\-\.](0?[1-9]|1[012])[\/\-\.](0?[1-9]|[12][0-9]|3[01])$/
	, date : /^(0?[1-9]|[12][0-9]|3[01])[\/\-\.](0?[1-9]|1[012])[\/\-\.](\d{4})$/
	, id : /^[a-zA-Z0-9]{6,18}$/
	, pwd : /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*<>])[A-Za-z\d!@#$%^&*<>]{8,18}$/
	, nick : /^[A-Za-z\dㄱ-ㅎ|ㅏ-ㅣ|가-힣]{2,8}$/
	, onlyLetterCommaNumber : /^[0-9a-zA-Z.]+$/
}

/**
 * Description : 쿠키 함수
 * author : qkrgksgh725
 */
var cmCookie = {
	set : function(name, value, expiredays){
		$.cookie(name, value, { expires: expiredays , path: '/' });
	},
	remove : function(name){
		$.removeCookie(name, { path: '/' });
	},
	get : function(name){
		return $.cookie(name);
	}
}


/**
 * Description : text 길이 제한 함수
 * author : qkrgksgh725
 * 예시 : 
 * class에 maxSize 또는 maxByteSize 선언되어 있어야 한다. <input type="text" class="input validate[maxSize[200]] 
 * $("#searchkeyword).limitText({
 * 		msgOutputUse : true  //message 출력 여부    defualt : false(출격 안함)
 *      , outputTrg :   $(".byte") // 출력 할 부분 지정 : defualt : 출력 할 부분 지정 안하면 출력 안함
 * });
 */
;(function ($) {
var methods = {
	init : function(options) {
		return this.each(function (){
			var $this = $(this),
				data = $this.data('limitText')
				msgOutputUse = (options && options.msgOutputUse) ? options.msgOutputUse : false,
				outputTrg = (options && options.outputTrg) ? options.outputTrg : undefined,
				settings = $.extend({
                }, options);
				var rulesParsing = $this.attr("class");
				var getRules = /validate\[(.*)\]/.exec(rulesParsing);
				
				if (!getRules)
					return false;
				var str = getRules[1];
				var rules = str.split(/\[|,|\]/);
				
				for (var i = 0; i < rules.length; i++) {
					rules[i] = rules[i].replace(" ", "");
					// Remove any parsing errors
					if (rules[i] === '') {
						delete rules[i];
					}
				}
				var max = 99999;
				var rule = "";
				var unit = "";
				for (var i = 0; i < rules.length; i++) {
					switch (rules[i]) {
						case "maxSize":
							rule = rules[i];
							max = rules[i + 1];
							unit = "char";
							break;
						case "maxByteSize":
							rule = rules[i]
							max = rules[i + 1];
							unit = "utf8";
							break;
						default:
					}
				}
				
				if(rule == "")
					return false;
				
				settings.max = max;
				settings.rule = rule;
				settings.unit = unit;
				
				if(msgOutputUse){
					settings.msg = {text1 : $.validLanguage.allRules[rule].alertText,
									text2 : $.validLanguage.allRules[rule].alertText2,
									text3 : $.validLanguage.allRules[rule].alertText3}
				}
				
				
				 $(this).data('limitText', {
                    'target': $this,
                    'settings': settings
                });

				$this.attr("maxLength", max);
				if(outputTrg != undefined){
					outputTrg.html("<b>"+ cmFunction.getLength($(this).val(), unit)+"</b>/"+max);
				}
				
				$this.on("keydown",function(e){
					var obj = $(this).data('limitText').settings;
					
					var cnt = cmFunction.getLength($(this).val(), obj.unit);
					
					if (cnt >= max) {
						if(obj.unit == "utf8"){
							$(this).attr("maxLength", cmFunction.getByteLength($(this).val(), max));
							$(this).val(cmFunction.getByteString($(this).val(), max));
						}else{
							$(this).val($(this).val().substring(0, max));
						}
						
					}else{
						if(obj.unit == "utf8"){
							$(this).attr("maxLength", max);
						}
					}
					
					var cnt = cmFunction.getLength($(this).val(), obj.unit);
					
					if(obj.outputTrg != undefined){
						obj.outputTrg.html("<b>"+cnt+"</b>/"+obj.max);
					}
					
				});
				
				$this.on("keyup",function(e){
					var obj = $(this).data('limitText').settings;
					if(obj.msgOutputUse){
						var cnt = cmFunction.getLength($(this).val(), obj.unit);
						
						if (cnt > max) {
							var msg = $this.attr("title")+"은(는) " + obj.msg.text1 + max + obj.msg.text2;
							if( obj.unit == "utf8"){
								var msg = $this.attr("title")+"은(는) " + obj.msg.text1 + Math.floor(max/3) + obj.msg.text2 + max + obj.msg.text3;
							}
							msgFnc.alert({text : msg
								, callBackConfirmFnc : function(){
									$this.focus();
									$this.trigger("keydown");
								  }
							});
							
						}
					}else{
						$(this).trigger("keydown");
					}
					
				});
				
				
		});
	}
	, 
}
$.fn.limitText = function(method) {
	if (methods[method]) {
        return methods[method].apply(this, Array.prototype.slice.call( arguments, 1 ));
    } else if (typeof method === 'object' || ! method) {
        return methods.init.apply(this, arguments);
    } else {
        $.error('Method ' + method + ' does not exist on limitText');
    }    
};
})(jQuery);


/**
 * Description : 검색엔진 함수
 * author : qkrgksgh725
 */
var srchFnc = {
	init : function(ipId, btnId){
	
		$("#"+ipId).data('searchInput', $("#"+ipId));

		$("#"+btnId).data('searchInput', $("#"+ipId));
	
		$("#"+ipId).unbind("keypress").bind("keypress", function(e){
			if (e.keyCode == 13) {
				srchFnc.search($(this).data('searchInput'));
			}
		});
		
		$("#"+btnId).unbind("click").bind("click", function(e){
				srchFnc.search($(this).data('searchInput'));
		});
	
	},
	search : function(obj){
		
		if(obj.val() == "" ){
			msgFnc.alert({text : cmMsg.alt.searchInput
				, callBackConfirmFnc : function(){
					obj.focus();
				  }
			});
			return false;
		}
		
		if(obj.oneValid()){
			var q = $.trim(obj.val());
			q=q.replace(/;/g,"&#59;");
			q=q.replace(/</g,"&lt;");
			q=q.replace(/>/g,"&gt;");
			q=q.replace(/%/g,"&#37;");
			
			
			
			var formTag = $("<form action=\"/v4po_search.do\" method=\"post\"><input type=\"hidden\" name=\"searchIdEW\" value=\""+encodeURI(q)+"\" /></form>").appendTo('body');
			var search = $("<input type=\"hidden\" name=\"searchIdw\" />").appendTo(formTag);
			search.val(obj.val());
			
			formTag.submit();
		}
		
		
		
	}
}

/**
 * Description : Url 호출 함수
 * author : qkrgksgh725
 */
var urlFnc = {
	/*메인화면*/
	goMain : function(){
		cmFunction.submit("/v4po_main.do");
	}
	/*로그인화면*/
	, goLogin : function(){
		var nextUrl = "";
		if(!cmFunction.isBlank(loginFnc.moveMenu)){
			nextUrl = loginFnc.moveMenu
		}else{
			if(typeof window.location.search != "undefined" && window.location.search != ""){
				if( window.location.pathname.includes("/anyId/login.do") ){
					nextUrl = decodeURIComponent(window.location.search.split("&")[0].split("=")[1]);
				}else{
					nextUrl = window.location.pathname + window.location.search;
				}
			}else{
				nextUrl = window.location.pathname;
			}
		}
		//20250308 anyid 추가
//		anyidAdaptor.ssoLoginPage(window.location.pathname,'3');
		cmFunction.submit("/v4po_usrlogin_a001.do",{nextUrl : nextUrl});
	}
	/*회원가입화면*/
	, goJoin : function(){
		cmFunction.submit("/v4po_usrcla_a002.do");
	}
	/*아이디찾기화면*/
	, goFindId : function(){
		cmFunction.submit("/v4po_usrid_s001.do");
	}
	/*비밀번호찾기화면*/
	, goFindPwd : function(){
		cmFunction.submit("/v4po_usrpwd_s001.do");
	}
	/*회원탈퇴화면*/
	, goSecsn : function(){
		cmFunction.submit("/v4po_usrout_a001.do");
	}
	/*이용약관화면*/
	, goAgree : function(){
		cmFunction.submit("/v4po_prcint_a001.do");
	}
	/*개인정보처리방침화면*/
	, goPrivacy : function(){
		cmFunction.submit("/v4po_prcint_a002.do");
	}
	/*이메일무단수집거부화면*/
	, goUnauthEmail : function(){
		cmFunction.submit("/v4po_prcint_a003.do");
	}
	/*저작권정책화면*/
	, goCpyrht : function(){
		cmFunction.submit("/v4po_prcint_a006.do");
	}
	/*브이월드소개화면*/
	, goIntrcn : function(){
		cmFunction.submit("/v4po_intbiz_a001.do");
	}
	/*마이포털화면*/
	, goMyPotal : function(){
		cmFunction.submit("/mypo/mypo_main_s001.do");
	}
	/*관심게시글*/
	, goItrstBbs : function(){
		cmFunction.submit("/mypo/mypo_brdItrst_s001.do");
	}
	/*관심주제도*/
	, goItrstMap : function(){
		cmFunction.submit("/mypo/mypo_bookmarkTheme_s001.do");
	}
	/*관심공간정보*/
	, goItrstSpceInfo : function(){
		cmFunction.submit("/mypo/mypo_data_s001.do");
	}
	/*관심오픈API*/
	, goItrstApi : function(){
		cmFunction.submit("/mypo/mypo_dtnaApi_s001.do");
	}
	/*읽지않음 알림*/
	, goNotRedngNtcn : function(){
		cmFunction.submit("/mypo/mypo_notify_s001.do");
	}
	/*관심공간분석API*/
	, goAnlsBkmk : function(){
		cmFunction.submit("/mypo/mypo_anlsBkmk_s001.do");
	}
	/*부동산중개업문의*/
	, goDtidFAQ : function(){
		cmFunction.submit("/v4po_brdfaq_s001.do?fqTab=98");
	}
}

/**
 * Description : mobile pagination
 * author : eblee
 */
var pageFnc= {
	resize: function(){
		if(window.innerWidth > 480)	return;
		
		var pList = $(".pages .pg");
		var pSize = pList.length;
		var pCur;
		
		if(pSize < 8)	return;
		
		for(var i = 0; i < pSize; ++i){
			if(pList[i].classList.contains("on") == true){
				pCur = i;
				break;
			}
		}
		
		for(var i = 1; i < pSize-1; ++i){
			if(i == pCur || i == pCur+1 || i == pCur-1){
				continue;
			}else if(i == pCur+2 || i == pCur-2){
				pList[i].innerText = "...";
			}else{
				pList[i].classList.add("hide");
			}
		}
	}
	, setPaging: function(){		
		var pList = $(".pages");
		
		if(window.innerWidth > 480){
			pList.get(1).classList.remove("hide");
			pList.get(2).classList.add("hide");
		}
		else{
			pList.get(1).classList.add("hide");
			pList.get(2).classList.remove("hide");
		}
	}
}