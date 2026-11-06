var menuFnc = {
	params : null
	, loginYn : "N"
	, locationYn : "N"
	, menuAcess : false
	, defHtml : {
		ul :  "<ul></ul>"
		, li : "<li></li>"
		, a : "<a></a>"
		, p : "<p></p>"
		, h2 : "<h2 id=\"depth1\" class=\"title\"></h2>"
		, div : "<div></div>"
		, main : "<a href=\"javascript:urlFnc.goMain();\" class=\"bt ico only home\" title=\"메인 바로가기\">메인</a>"
		, button : "<button type=\"button\" class=\"bt ico arrow only\">메뉴선택</button>"
		, button_itrst : "<button type=\"button\" class=\"bt ico bookmark only onoff\">관심</button>"
		, span : "<span></span>"
		, span_lock : "<span class=\"bt ico lock min only\">로그인필요</span>"
	}
	, create : {
		ul : function(classNm){
			var ul = $(menuFnc.defHtml.ul);
			if(classNm != ""  && classNm != null && classNm != undefined){
				ul.addClass(classNm);
			}
			return ul;
		}
		, li : function(classNm){
			var li	= $(menuFnc.defHtml.li);
			if(classNm != ""  && classNm != null && classNm != undefined){
				li.addClass(classNm);
			}
			return li;
		}
		, a : function(url, nm, onCls, lock, siteMapYn){
			var a = $(menuFnc.defHtml.a);
			a.text(nm);
			if(lock == "Y"){
				$(menuFnc.defHtml.span_lock).appendTo(a);
			}
			
			if(nm == "지하시설물 조회"){
				a.attr("href","javascript:menuFnc.goToUndr();");
			}else if(siteMapYn == "Y"){
				a.attr("href","javascript:menuFnc.move('"+url+"','Y');");
			}else{
				a.attr("href","javascript:menuFnc.move('"+url+"');");
			}
			a.addClass("menu");
			//25.09.27 anyid 장애로 인해 잠시 막아둠 - 최지성
			if(nm == "로그인") {
				a.attr("href", "javascript:anyidAdaptor.ssoLoginPage(window.location.pathname+window.location.search,'3')");
			} else if (nm == "내 토지찾기" || nm == "조상땅찾기" || nm == "지하시설물 조회") {
			    if (!isNaN(url)) {
			        a.append("<p class='btPop' style='justify-content: center;'/>");
			    } else {
			        a.append("<p class='btPop'/>");
			    }
			}
			
			
			
			if(onCls != undefined && onCls != null && onCls != ""){
				a.addClass("on");
			}
			
			return a;
		}
		, p : function(url, nm, onCls, lock, siteMapYn){
			var p = $(menuFnc.defHtml.p);
			p.text(nm);
			if(lock == "Y"){
				$(menuFnc.defHtml.span_lock).appendTo(p);
			}
			if(url != undefined && url != null && url != ""){
				if(siteMapYn == "Y"){
					p.attr("href","javascript:menuFnc.move('"+url+"','Y');");
				}else{
					p.attr("href","javascript:menuFnc.move('"+url+"');");
				}
			}
			p.addClass("menu");
			
			if(onCls != undefined && onCls != null && onCls != ""){
				p.addClass("on");
			}
			
			return p;
		}
		, div : function(classNm, idNm){
			var div	= $(menuFnc.defHtml.div);
			div.addClass("one");
			if(classNm != "" && classNm != null && classNm != undefined){
				div.addClass(classNm);
			}
			if(idNm != "" && idNm != null && idNm != undefined){
				div.attr("id",idNm);
			}
			return div;
			
		}
		, span : function(nm){
			var span = $(menuFnc.defHtml.span);
			span.text(nm);
			return span;
		}
		, itrstButton : function(idx, chkYn){
			var button = $(menuFnc.defHtml.button_itrst);
			button.attr("onClick","javascript:menuFnc.saveItrSt('"+idx+"',$(this));");
			if(chkYn == "Y"){
				button.addClass("on");
			}
			
			return button;
		}
	}
	, set : function(){
		
		cmFunction.ajaxSubmit(
			"/v4po_menu_a001.do"
			, []
			, function(data){
				if(data.loginInfo != null){
					menuFnc.loginYn = "Y";
					menuFnc.setItrst();
				}
				params = data.menuList;
				
				menuFnc.menuCreate();
				menuFnc.sitemapCreate();
				menuFnc.lnbCreate();
				menuFnc.locationCreate();
//				2024-09-04 mobile view add
				menuFnc.mobileSet();
			}
			, null
		);
	}
	, setItrst : function(){
		
		cmFunction.ajaxSubmit(
			"/v4po_itrst_a001.do"
			, []
			, function(data){
				if(Number(data.itrstCnt.readcnt) > 0){
					$("#headerMyPoBtn").addClass("new");
				}
				$(".sitemap").find("#notRedngNtcnCnt").html(data.itrstCnt.readcnt);
		        $("#login-after").find("#notRedngNtcnCnt").html(data.itrstCnt.readcnt);
				
				$("#myPoReadCnt").html(data.itrstCnt.readcnt);
				$("article[class='myportal']").find("#readCnt").html(data.itrstCnt.readcnt);
				$("article[class='myportal']").find("#bbsCnt").html(data.itrstCnt.bbscnt);
		        $("article[class='myportal']").find("#mapCnt").html(data.itrstCnt.mapcnt);
		        $("article[class='myportal']").find("#dataCnt").html(data.itrstCnt.datacnt);
		        $("article[class='myportal']").find("#apiCnt").html(data.itrstCnt.apicnt);
		        $("article[class='myportal']").find("#anlsCnt").html(data.itrstCnt.anlscnt);


		        $("#login-after").find("#bbsCnt").html(data.itrstCnt.bbscnt);
		        $("#login-after").find("#mapCnt").html(data.itrstCnt.mapcnt);
		        $("#login-after").find("#dataCnt").html(data.itrstCnt.datacnt);
		        $("#login-after").find("#apiCnt").html(data.itrstCnt.apicnt);
		        $("#login-after").find("#anlsCnt").html(data.itrstCnt.anlscnt);

				
			}
			, null
		);
	}
	, subMenuCheck : function(idx){
		
		var subMenuYn = "N";
		
		for (var i = idx+1; i < params.length; i++) {
			if( params[idx+1].menu_level != params[i].menu_level){
				break;
			}
			if( params[i].menu_yn == "Y"){
				subMenuYn = "Y";
				break;
			}
		}
		return subMenuYn;
	}
	, menuCreate : function(){
		$("#headerMenu").html(menuFnc.defHtml.ul);
		var ul = $("#headerMenu > ul");
		var ul2, ul3, li, p;
		var headerbln = false;
		var header2bln = false;
		var createLi = true;
		$.each(params, function(idx, item){
			if(item.menu_yn == "Y"){
				if(item.menu_level == 1){
					if(item.top_menu_yn == "Y"){
						li = menuFnc.create.li("toggle").appendTo(ul);
						
						if(!cmFunction.isBlank(item.url)){
							menuFnc.create.a(item.url,item.menu_nm).appendTo(li);
						}else{
							menuFnc.create.a(idx, item.menu_nm).appendTo(li);
							//menuFnc.create.p(item.url,item.menu_nm).appendTo(li);
						}
						
						if(params[idx+1] != undefined && params[idx+1].menu_level == 2){
							if(menuFnc.subMenuCheck(idx) == "Y"){
								ul2 = menuFnc.create.ul("dropbox").appendTo(li);
							}else{
								createLi = false;
							}
						}
					}else{
						headerbln = true;
					}
				}else if(item.menu_level == 2){
					if(!headerbln){
						if(item.top_menu_yn == "Y"){
							if(item.lgn_yn == "Y" &&  cmFunction.isBlank(item.authrt_group_cd)){
								// 2025-01-15
								// 기업회원이 아닌경우 나의 기업정보관리 미표출
							}else{
								if(!createLi){
									createLi = true;
									ul2 = menuFnc.create.ul("dropbox").appendTo(li);
								}
								li = menuFnc.create.li().appendTo(ul2);
								
								if(!cmFunction.isBlank(item.url)){
									menuFnc.create.a(item.url,item.menu_nm).appendTo(li);
								}else{
									menuFnc.create.a(idx, item.menu_nm).appendTo(li);
									//menuFnc.create.p(item.url,item.menu_nm).appendTo(li);
								}
								
								if(params[idx+1] != undefined && params[idx+1].menu_level > 2){
									if(menuFnc.subMenuCheck(idx) == "Y"){
										ul3 = menuFnc.create.ul("submenu").appendTo(li);
									}
								}		
							}
						}else{
							header2bln = true;
						}
					}
				}else if(item.menu_level == 3){
					if(!headerbln && !header2bln){
						if(item.top_menu_yn == "Y"){
							if(item.lgn_yn == "Y" &&  cmFunction.isBlank(item.authrt_group_cd)){
								// 2025-01-15
								// 기업회원이 아닌경우 나의 기업정보관리 미표출								
							}else{
								li = menuFnc.create.li().appendTo(ul3);
								if(!cmFunction.isBlank(item.url)){
									menuFnc.create.a(item.url,item.menu_nm).appendTo(li);
								}else{
									menuFnc.create.a(idx,item.menu_nm).appendTo(li);
								}
							}
						}
					}
				}
			}
				
			if(idx == params.length-1 || (params[idx+1] != undefined && params[idx+1].menu_level == 1)){
				headerbln = false;
				header2bln = false;
			}
		});
	}
	, saveItrSt : function(idx, obj){
		var mode = "I";
		var msg = "관심메뉴로 등록되었습니다.";
		if(obj.hasClass("on")){
			mode = "D";
			msg = "관심메뉴로 취소되었습니다.";
		}
		cmFunction.ajaxSubmit(
			"/v4po_menu_a002.do"
			, {itrstMenuId : params[idx].menu_id, mode : mode}
			, function(data){
				msgFnc.alert(msg);
			}
		);
	}
	, sitemapCreate : function(){
		$("#sitemapMenu").html(menuFnc.defHtml.ul);
		var ul = $("#sitemapMenu > ul");
		var ul2, ul3, li, p;
		var createLi = true;
		$.each(params, function(idx, item){
			if(item.menu_yn == "Y"){
				if(item.menu_level == 1){
					li = menuFnc.create.li("toggle").appendTo(ul);
					
					if(!cmFunction.isBlank(item.url)){
						menuFnc.create.a(item.url, item.menu_nm, "", item.lgn_yn, "Y").appendTo(li);
						if(item.bkmk_yn == "Y" && menuFnc.loginYn == "Y" ){
							//$(menuFnc.defHtml.button_itrst).appendTo(li);
							menuFnc.create.itrstButton(idx, item.itrst_yn).appendTo(li);
						}
					}else{
						menuFnc.create.a(idx, item.menu_nm, "", item.lgn_yn, "Y").appendTo(li);
						//menuFnc.create.p(item.url,item.menu_nm,"",item.lgn_yn).appendTo(li);
					}
					
					if(params[idx+1] != undefined && params[idx+1].menu_level == 2){
						if(menuFnc.subMenuCheck(idx) == "Y"){
							$("<button type=\"button\" class=\"bt ico only arrow\">메뉴 열고닫기</button>").appendTo(li);
							ul2 = menuFnc.create.ul("slipbox").appendTo(li);
						}else{
							createLi = false;
						}
					}
				}else if(item.menu_level == 2){
					if(!(item.menu_nm=="지식추론AI" && cmFunction.isBlank(item.authrt_group_cd))){
						if(!createLi){
							createLi = true;
							ul2 = menuFnc.create.ul("slipbox").appendTo(li);
						}
						
						li = menuFnc.create.li().appendTo(ul2);
						
						if(!cmFunction.isBlank(item.url) ){
								menuFnc.create.a(item.url,item.menu_nm,"",item.lgn_yn, "Y").appendTo(li);
								if(item.bkmk_yn == "Y" && menuFnc.loginYn == "Y"&& !cmFunction.isBlank(item.authrt_group_cd)){
									//$(menuFnc.defHtml.button_itrst).appendTo(li);
									menuFnc.create.itrstButton(idx, item.itrst_yn).appendTo(li);
								}
						}else{
							menuFnc.create.a(idx, item.menu_nm, "", item.lgn_yn, "Y").appendTo(li);
							//menuFnc.create.p(item.url,item.menu_nm,"",item.lgn_yn).appendTo(li);
						}
						
						if(params[idx+1] != undefined && params[idx+1].menu_level > 2){
							if(!cmFunction.isBlank(item.authrt_group_cd) || item.menu_id.includes("_106") ){
								if(menuFnc.subMenuCheck(idx) == "Y"){
									ul3 = menuFnc.create.ul("submenu").appendTo(li);
								}
							}
						}
					}
				}else if(item.menu_level == 3){
					if(!cmFunction.isBlank(item.authrt_group_cd) || item.menu_id.includes("_106") ){
						li = menuFnc.create.li().appendTo(ul3);
						if(!cmFunction.isBlank(item.url)){
							menuFnc.create.a(item.url,item.menu_nm,"",item.lgn_yn, "Y").appendTo(li);
						}else{
							menuFnc.create.a(idx,item.menu_nm,"",item.lgn_yn, "Y").appendTo(li);
						}
						if(item.bkmk_yn == "Y" && menuFnc.loginYn == "Y"){
							//$(menuFnc.defHtml.button_itrst).appendTo(li);
							menuFnc.create.itrstButton(idx, item.itrst_yn).appendTo(li);
						}
					}
				}
			}
			
		});
	}
	, lnbCreate : function(){
		var trgLnb = null;
		var lnbList = null;
		
		$("#lnbMenu").html(menuFnc.defHtml.main);
		
		$.each(params, function(idx, item){
			if(window.location.pathname == item.url){
				trgLnb = item;
			}
		});
		
		if(trgLnb != null){
			if(trgLnb.menu_yn == "Y"){
				lnbList = trgLnb.path.split(",");
			}else{
				var items = trgLnb.path.split(",");
				lnbList = items.slice(0, items.length-1);
			}
			var h2;
			$.each(lnbList, function(idx, item){
				var div;
				var ul;
				if(idx == 0){
					h2 = $(menuFnc.defHtml.h2).appendTo("#lnbMenu");
					$.each(params, function(idx2, item2){
						if(item == item2.menu_id){
							menuFnc.create.a((cmFunction.isBlank ? idx2 :  item2.url),item2.menu_nm).appendTo(h2);
							return false;
						}
					});
				}else{
					div = menuFnc.create.div("toggle","depth"+(idx+1)).appendTo("#lnbMenu");
					
					var cnt = 0;
					$.each(params, function(idx2, item2){
						if(lnbList[idx] == item2.menu_id){
							cnt = 1;
							menuFnc.create.p(item2.url,item2.menu_nm).appendTo(div);
							return false;
						}
					});
					if(cnt == 0){
						menuFnc.create.p("","선택").appendTo(div);
					}
					
					
					menuFnc.create.p().appendTo(div);
					$(menuFnc.defHtml.button).appendTo(div);
					ul = menuFnc.create.ul("dropbox").appendTo(div);
					
					$.each(params, function(idx2, item2){
						if(lnbList[idx-1] == item2.up_menu_id && item2.menu_yn == 'Y'){
							var chkYn = "";
							if(lnbList[idx] == item2.menu_id){
								chkYn = "Y";
							}
							var li = menuFnc.create.li().appendTo(ul);
							menuFnc.create.a((cmFunction.isBlank ? idx2 :  item2.url), item2.menu_nm, chkYn).appendTo(li);
						}
					});
				}
			});
		}
		
		$.each($("#lnbMenu > div"), function(idx, item){
			$(item).find("p").click(function(){
				$(item).find("button").click();
			});
		});
		
	}
	, locationCreate : function(){
		var trgLnb = null;
		var lnbList = null;
		var lastMenuNm = "";
		$.each(params, function(idx, item){
			if(window.location.pathname == item.url){
				trgLnb = item;
			}
		});
		
		if(trgLnb != null){
			lnbList = trgLnb.path.split(",");
			$.each(lnbList, function(idx, item){
				$.each(params, function(idx2, item2){
					if(item == item2.menu_id && item2.menu_yn == 'Y'){
						menuFnc.create.span(item2.menu_nm).appendTo("#locationMenu");
						lastMenuNm = item2.menu_nm;
						return false;
					}
				});
			});
		}
		
		if(menuFnc.locationYn == "Y"){
			document.title = "브이월드 "+lastMenuNm;
		}
	}
	, move : function(url, siteMapYn, mvInfo){
		if(!cmFunction.isBlank(url)){
			if(cmFunction.isNumber(url)){
				var ownLvl = "";
				for (var i = url; i < params.length; i++) {
					if( i == url ){
						ownLvl = params[i].menu_level;
					}else if(ownLvl == params[i].menu_level){
						break;
					}
					
					if(!cmFunction.isBlank(params[i].url)){
						url = params[i].url;
						break;
					}
				}
			}
			
			$.each(params, function(idx, item){
				if(url == item.url){
					
						//로그인 필요한 메뉴일때
					if(item.lgn_yn == "Y" && menuFnc.loginYn == "N"){
						if(cmFunction.isBlank(siteMapYn)){
							msgFnc.alert({ text : '로그인이 필요한 메뉴입니다.<br/>로그인하시면 해당서비스로 이동합니다.'                       
									     , callBackConfirmFnc : function(){loginFnc.def(item.url);}
							});                                                 
							return false;
						}else{
							msgFnc.alert({ text : '로그인이 필요한 메뉴입니다.<br/>로그인하시면 해당서비스로 이동합니다.<br/>로그인 페이지로 이동합니다.'                       
								// 공장인허가 소스 수정 시작	   
//								, callBackConfirmFnc : function(){loginFnc.def(item.url); urlFnc.goLogin();}
								, callBackConfirmFnc : function(){loginFnc.def(item.url); anyidAdaptor.ssoLoginPage(window.location.pathname+window.location.search,'3')}
								// 공장인허가 소스 수정 끝
							
							});                                                 
							return false;
						}
					}
					
					if(item.lgn_yn == "Y" && menuFnc.loginYn == "Y" && cmFunction.isBlank(item.authrt_group_cd)){
						msgFnc.alert('권한이 필요한 메뉴입니다.');                                                 
						return false;
					}
					var target = null;
					if(item.fnct_se_cd == "MGC002"){
						target = "_blank";
					}
					
					/* 로컬, 개발서버용 jaeha.park*/
					var goUrl = item.url.replace("https://map.vworld.kr",cmAppUrl.map);
					
					/* 20251109 DT 임시주석
					if( goUrl.indexOf('https://v-world.github.io/Utilization-Model/') != -1 ){
						cmFunction.submit(goUrl, "", "get", "", target);
					}else{
						cmFunction.submit(goUrl, "", "", "", target);
					}
					*/
					
					//test
					if(mvInfo){
						cmFunction.submit(goUrl, mvInfo, "", "", target);
					}else{
						if( goUrl.indexOf('https://v-world.github.io/Utilization-Model/') != -1 ){
							cmFunction.submit(goUrl, "", "get", "", target);
						}else{
							cmFunction.submit(goUrl, "", "", "", target);
						}
					}
					
					return false;
				}else{
					/* 2024-09-04 임의로 설정해놓은 url yhkim*/
					if(url.includes('mode=MAPW201')){
						cmFunction.submit(url, "", "", "", "_blank");						
					}
				}
			});
		}
	}
//	2024-09-04 mobile view add writing by yhkim
	, mobileSet : function(){
		if(cmFunction._isMobile()){
			$('.mDtkmap').addClass('hide');
			$('a[href]').attr('href', function(i, val){return val.replace('mode=MAPD101', 'mode=MAPW201')});
		}else{
			$('.mDtkmap').removeClass('hide');
		}
	}
//	2025-03-14 fctrMap view add writing by yhkim
	, goToFctr : function(){
		if(cmFunction._isMobile()){
			msgFnc.alert('모바일에서는 서비스하지 않습니다.');       
			return false;
		}else{
			if(menuFnc.loginYn == "Y"){
				window.open("https://pss.vworld.kr/fctrMapMain.do", "_blank", "width=1920, height=1200");
			}else{
				msgFnc.alert({ text : '로그인이 필요한 메뉴입니다.<br/>로그인하시면 해당서비스로 이동합니다.<br/>로그인 페이지로 이동합니다.'                       
//				, callBackConfirmFnc : function(){loginFnc.def("https://pss.vworld.kr/fctrMapMain.do",'Y');}
				, callBackConfirmFnc : function(){anyidAdaptor.ssoLoginPage(window.location.pathname+window.location.search,'3')}
				});                                                 
				return false;
			}
		}
	}
// 2025-10-31 mymap view add writing by yhkim
	,goToMyMap : function(){
		if(cmFunction._isMobile()){
			msgFnc.alert('모바일에서는 서비스하지 않습니다.');       
			return false;
		}else{
			if(menuFnc.loginYn == "Y"){
				window.open("https://map.vworld.kr/map/dtkmap.do?qCode=16", "_self");
			}else{
				msgFnc.alert({ text : '로그인이 필요한 메뉴입니다.<br/>로그인하시면 해당서비스로 이동합니다.<br/>로그인 페이지로 이동합니다.'                       
				, callBackConfirmFnc : function(){anyidAdaptor.ssoLoginPage("https://map.vworld.kr/map/dtkmap.do?qCode=16",'3')}
				});                                                 
				return false;
			}
		}
	}
	
	, goToUndr : function(){
		if(cmFunction._isMobile()){
			msgFnc.alert('모바일에서는 서비스하지 않습니다.');       
			return false;
		}else{
			if(menuFnc.loginYn == "Y"){
				window.open("https://pss.vworld.kr/underMap.do", "_blank", "width=1920, height=1200"); // 운영용
//				window.open("http://localhost:8780/underMap.do", "_blank", "width=1920, height=1200"); // 로컬용
			}else{
				msgFnc.alert({ text : '로그인이 필요한 메뉴입니다.<br/>로그인하시면 해당서비스로 이동합니다.<br/>로그인 페이지로 이동합니다.'
					, callBackConfirmFnc : function(){anyidAdaptor.ssoLoginPage(window.location.pathname+window.location.search,'3')}
					});                                                 
					return false;
			}
		}
	}
}