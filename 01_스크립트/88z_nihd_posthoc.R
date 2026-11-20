# 88z_nihd — 비허혈 심장질환 사망(NIHD) 역방향(불명확 사인 비율 가설 +, 관측 −) 사후 검정(2026-11-12, 결과를 본 뒤 수행 = post hoc). 88z_htnd 복제, 공유 원본 무수정.
#  사용(01_스크립트/): TAG=NIHD ST_VER=std3 ST_THREADS=1 ST_GRAPH=<593> Rscript 88z_nihd_posthoc.R
#  Q0 주모형 재적합 / Q1 불명확 사인 비율 제외 / Q2 단독(+강제통제) / Q3 지역 간·내 분해 / Q4 넓은 결과 I26-I51+R00-R99(E=02_패널/NIHR_Estd2.csv) 불명확 비율 제외 / Q5 Q4 + 불명확 비율 / Q6 접근 축(내과·독거) 제외
#  산출: results_std3/S45_coding_<an>.csv, S45_coding_area.csv(Q0·Q1·Q4 지역 공간 RR)
suppressPackageStartupMessages({library(INLA);library(sf);library(spdep);library(jsonlite)})
TAG<-Sys.getenv("TAG");stopifnot(nzchar(TAG));VER<-Sys.getenv("ST_VER",unset="std");SUF<-if(nzchar(VER))paste0("_",VER) else ""
ROOT<-normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),".."))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
OUTD<-file.path(ROOT,"04_분석",TAG);RES<-file.path(OUTD,paste0("results",SUF))
inla.setOption(num.threads="1:1")
LOG<-function(...)cat(sprintf("[88g %s %s] ",TAG,format(Sys.time(),"%H:%M:%S")),sprintf(...),"\n",sep="")
S<-fromJSON(file.path(OUTD,sprintf("config_%s%s.json",TAG,SUF)),simplifyVector=TRUE)
INFO<-fromJSON(file.path(OUTD,sprintf("panel_INFO_%s%s.json",TAG,SUF)))
DD<-read.csv(file.path(OUTD,sprintf("panel_%s%s.csv",TAG,SUF)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
HB<-readLines(file.path(OUTD,sprintf("HM_best_%s%s.txt",TAG,SUF)));kv<-function(k)sub(paste0("^",k,"="),"",grep(paste0("^",k,"="),HB,value=TRUE)[1])
MAINFAM<-kv("main_family");BEST<-kv("best_set");FORCED<-S$forced;SETS<-lapply(S$sets_after_vif,as.character);HYPV<-SETS[[BEST]];MAINV<-unique(c(HYPV,FORCED))
ROB<-read.csv(file.path(RES,"S7_multiverse_summary.csv"),stringsAsFactors=FALSE);ROBV<-ROB$cov[ROB$robust];NR<-length(ROBV)
M3<-read.csv(file.path(RES,"S3_main_IRR.csv"),stringsAsFactors=FALSE);msign<-setNames(sign(log(M3$IRR)),M3$cov)
FOCAL<-Sys.getenv("FOCAL",unset=if(NR)ROBV[1] else HYPV[1])
LOG("family %s, set %s (%d hyp + %d forced), robust %d (%s), focal %s",MAINFAM,BEST,length(HYPV),length(FORCED),NR,paste(ROBV,collapse=";"),FOCAL)

G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);n<-nrow(G)
g<-inla.read.graph(file.path(RES,sprintf("nb_%s.graph",TAG)));stopifnot(g$n==n)
DD<-DD[order(DD$year,match(DD$fbd_region,G$region)),];DD$area<-match(DD$fbd_region,G$region);Y0<-min(DD$year);DD$time<-DD$year-Y0+1;DD$yiid<-DD$time;DD$id<-seq_len(nrow(DD))
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
CF<-list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001)
SPf<-function(gr="g")sprintf("f(area,model='bym2',graph=%s,scale.model=TRUE,constr=TRUE,hyper=pc)",gr)
TI<-"f(time,model='rw1',scale.model=TRUE,hyper=pcp)";IT<-"f(yiid,model='iid',hyper=pcp)"
bt<-function(v)sprintf("`%s`",v)
irr<-function(m,v){r<-m$summary.fixed[v,,drop=FALSE];pg<-1-inla.pmarginal(0,m$marginals.fixed[[v]])
  data.frame(cov=v,IRR=round(exp(r$mean),3),lo=round(exp(r$`0.025quant`),3),hi=round(exp(r$`0.975quant`),3),P_gt1=round(pg,3),cred=(r$`0.025quant`>0|r$`0.975quant`<0),stringsAsFactors=FALSE)}
M6<-read.csv(file.path(RES,"S6_spatial_RR.csv"),stringsAsFactors=FALSE);hot0<-M6$fbd_region[M6$class=="hotspot"]
rdp<-function(f){x<-read.csv(file.path(RES,f),fileEncoding="UTF-8",stringsAsFactors=FALSE);x$fbd_region<-enc2utf8(x$fbd_region);x}
mrg<-function(d,X,cols){d<-d[,setdiff(names(d),cols)];d<-merge(d,X[,c("year","fbd_region",cols)],by=c("year","fbd_region"),all.x=TRUE,sort=FALSE);d[order(d$id),]}
fitX<-function(vars,data,fam=MAINFAM,ti=TI,extra=character(0),sp=SPf(),cfg=FALSE){
  rhs<-c("1",bt(vars),extra,sp,ti,IT);rhs<-rhs[nzchar(rhs)];form<-as.formula(paste("cases ~",paste(rhs,collapse="+")))
  m<-tryCatch(inla(form,family=fam,data=data,E=E,control.fixed=CF,control.compute=list(waic=TRUE,config=cfg),control.predictor=list(compute=TRUE,link=1),
    control.inla=list(control.vb=list(emergency=50)),verbose=FALSE),error=function(e){message("fail: ",conditionMessage(e));NULL})
  if(is.null(m))m<-tryCatch(inla(form,family=fam,data=data,E=E,control.fixed=CF,control.compute=list(waic=TRUE,config=cfg),control.predictor=list(compute=TRUE,link=1),
    control.inla=list(control.vb=list(emergency=50),int.strategy="eb",strategy="gaussian"),verbose=FALSE),error=function(e){message("robust fail: ",conditionMessage(e));NULL})
  m}

summ<-function(an,item,m,note,vars){
  if(is.null(m)){LOG("%s FAILED",an);return(invisible())}
  r<-do.call(rbind,lapply(intersect(vars,rownames(m$summary.fixed)),function(v)irr(m,v)))
  out<-data.frame(analysis=an,item=item,r,WAIC=round(m$waic$waic,1),note=note,stringsAsFactors=FALSE)
  write.csv(out,file.path(RES,sprintf("S45_coding_%s.csv",an)),row.names=FALSE,fileEncoding="UTF-8")
  for(i in seq_len(nrow(out)))LOG("%-14s %-40s %.3f (%.3f-%.3f)%s",an,out$cov[i],out$IRR[i],out$lo[i],out$hi[i],if(out$cred[i])"*" else "")
  invisible(m)}
arear<-function(m){s<-m$summary.random$area[1:n,];data.frame(fbd_region=G$region,RR=exp(s$mean),P_gt1=sapply(m$marginals.random$area[1:n],function(x)1-inla.pmarginal(0,x)))}
ILL<-"ill_defined_death_share";stopifnot(ILL%in%MAINV)
NOILL<-setdiff(MAINV,ILL)
m0<-summ("Q0_main_refit","reference",fitX(MAINV,DD),"principal model refit",MAINV)
m1<-summ("Q1_without_illdefined","certification",fitX(NOILL,DD),"principal model without ill-defined cause share",NOILL)
summ("Q2_illdefined_alone","overadjustment",fitX(c(ILL,FORCED),DD),"ill-defined cause share + forced covariates only",c(ILL,FORCED))
d3<-DD;mu<-ave(d3[[ILL]],d3$area);d3$ill_between<-mu;d3$ill_within<-d3[[ILL]]-mu
summ("Q3_between_within","decomposition",fitX(c(NOILL,"ill_between","ill_within"),d3),"ill-defined share split into district mean (between) and yearly deviation (within)",c("ill_between","ill_within"))
B<-read.csv(file.path(OUTD,"..","NIHR","panel_NIHR.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);B$fbd_region<-enc2utf8(B$fbd_region)
EB<-read.csv(file.path(ROOT,"02_패널","NIHR_Estd2.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);EB$fbd_region<-enc2utf8(EB$fbd_region)
db<-DD[,setdiff(names(DD),c("cases","E"))]
db<-merge(db,B[,c("year","fbd_region","cases")],by=c("year","fbd_region"),sort=FALSE);db<-merge(db,setNames(EB[,c("year","fbd_region","E_std2")],c("year","fbd_region","E")),by=c("year","fbd_region"),sort=FALSE)
db<-db[order(db$id),];stopifnot(nrow(db)==nrow(DD),!anyNA(db$cases),!anyNA(db$E));LOG("broad outcome cases %d (main %d)",sum(db$cases),sum(DD$cases))
m4<-summ("Q4_broad_outcome","outcome_definition",fitX(NOILL,db),"outcome = I26-I51 + R00-R99 deaths, E from national age-specific rates of both (18 bands)",NOILL)
summ("Q5_broad_plus_illdefined","outcome_definition",fitX(MAINV,db),"broad outcome + ill-defined cause share",MAINV)
summ("Q6_access_axis_removed","overadjustment",fitX(setdiff(MAINV,c("im_specialists_per_100k","older_single_household_share")),DD),"principal model without internal-medicine specialists and older single households",MAINV)
if(!is.null(m0)&&!is.null(m1)&&!is.null(m4)){a<-Reduce(function(x,y)merge(x,y,by="fbd_region"),list(setNames(arear(m0),c("fbd_region","RR_main","P_main")),setNames(arear(m1),c("fbd_region","RR_noill","P_noill")),setNames(arear(m4),c("fbd_region","RR_broad","P_broad"))))
  write.csv(a,file.path(RES,"S45_coding_area.csv"),row.names=FALSE,fileEncoding="UTF-8")
  LOG("area RR Spearman main vs noill %.3f, main vs broad %.3f",cor(a$RR_main,a$RR_noill,method="spearman"),cor(a$RR_main,a$RR_broad,method="spearman"))}
LOG("done")
