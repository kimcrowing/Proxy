/*
领京豆额外奖励
活动入口：京东APP首页-领京豆
cron "18 19,21 * * *" script-path=https://raw.githubusercontent.com/Aaron-lv/sync/jd_scripts/jd_bean_home.js, tag=领京豆额外奖励

 */
const $ = new Env('领京豆-升级赚豆');
const notify = $.isNode() ? require('./sendNotify') : '';
//Node.js用户请在jdCookie.js处填写京东ck;
const jdCookieNode = $.isNode() ? require('./jdCookie.js') : '';
//IOS等用户直接用NobyDa的jd cookie
const ua = require('./USER_AGENTS');
let cookiesArr = [], cookie = '', uuid = '', message;
if ($.isNode()) {
    Object.keys(jdCookieNode).forEach((item) => {
        cookiesArr.push(jdCookieNode[item])
    })
    if (process.env.JD_DEBUG && process.env.JD_DEBUG === 'false') console.log = () => {
    };
} else {
    cookiesArr = [$.getdata('CookieJD'), $.getdata('CookieJD2'), ...jsonParse($.getdata('CookiesJD') || "[]").map(item => item.cookie)].filter(item => !!item);
}
const JD_API_HOST = 'https://api.m.jd.com/';
!(async () => {
    $.newShareCodes = []
    if (!cookiesArr[0]) {
        $.msg($.name, '【提示】请先获取京东账号一cookie\n直接使用NobyDa的京东签到获取', 'https://bean.m.jd.com/bean/signIndex.action', { "open-url": "https://bean.m.jd.com/bean/signIndex.action" });
        return;
    }
    for (let i = 0; i < cookiesArr.length; i++) {
        if (cookiesArr[i]) {
            cookie = cookiesArr[i];
            $.UserName = decodeURIComponent(cookie.match(/pt_pin=([^; ]+)(?=;?)/) && cookie.match(/pt_pin=([^; ]+)(?=;?)/)[1])
            $.index = i + 1;
            $.isLogin = true;
            $.nickName = '';
            message = '';
            uuid = randomString();
            $.UA = ua.UARAM ? ua.UARAM() : ua.USER_AGENT;
            $.av = $.UA.split(';')[2];
            await TotalBean();
            console.log(`\n******开始【京东账号${$.index}】${$.nickName || $.UserName}*********\n`);
            if (!$.isLogin) {
                $.msg($.name, `【提示】cookie已失效`, `京东账号${$.index} ${$.nickName || $.UserName}\n请重新登录获取\nhttps://bean.m.jd.com/bean/signIndex.action`, { "open-url": "https://bean.m.jd.com/bean/signIndex.action" });

                if ($.isNode()) {
                    await notify.sendNotify(`${$.name}cookie已失效 - ${$.UserName}`, `京东账号${$.index} ${$.UserName}\n请重新登录获取cookie`);
                }
                continue
            }
            await jdBeanHome();
        }
    }

})()
    .catch((e) => {
        $.log('', `❌ ${$.name}, 失败! 原因: ${e}!`, '')
    })
    .finally(() => {
        $.done();
    })

async function jdBeanHome() {
    try {
        $.doneState = false
        $.flag = true
        do {
            await doTask2()
            await $.wait(3000)
        } while (!$.doneState && $.flag)
        if ($.flag) {
            await $.wait(1000)
            await award("feeds")
            await $.wait(1000)
            await getUserInfo()
            await $.wait(1000)
            //await getTaskList();
            //await receiveJd2();
        }
        //await morningGetBean()
        await $.wait(1000)

        await beanTaskList(1)
        await $.wait(1000)
        await queryCouponInfo()
        $.doneState = false
        let num = 0
        do {
            await $.wait(2000)
            await beanTaskList(2)
            num++
        } while (!$.doneState && num < 5)
        await $.wait(2000)
        if ($.doneState) await beanTaskList(3)

        await showMsg();
    } catch (e) {
        $.logErr(e)
    }
}

// 早起福利
function morningGetBean() {
    return new Promise(resolve => {
        $.post(taskBeanUrl('morningGetBean', { "fp": "-1", "shshshfp": "-1", "shshshfpa": "-1", "referUrl": "-1", "userAgent": "-1", "jda": "-1", "rnVersion": "3.9" }), (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} morningGetBean API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.data?.awardResultFlag === "1") {
                            console.log(`早起福利领取成功：${data.data.bizMsg}`)
                        } else if (data.data?.awardResultFlag === "2") {
                            console.log(`早起福利领取失败：${data.data.bizMsg}`)
                        } else {
                            console.log(`早起福利领取失败：${data.data.bizMsg}`)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve(data);
            }
        })
    })
}

// 升级领京豆任务
async function beanTaskList(type) {
    return new Promise(resolve => {
        $.post(taskBeanUrl('beanTaskList', { "viewChannel": "AppHome", "beanVersion": 1 }), async (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} beanTaskList API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (!data.errorMessage) {
                            switch (type) {
                                case 1:
                                    console.log(`当前等级:${data.data.curLevel} 下一级可领取:${data.data.nextLevelBeanNum || 0}京豆`)
                                    if (data.data.viewAppHome) {
                                        if (!data.data.viewAppHome.takenTask) {
                                            console.log(`去做[${data.data.viewAppHome.mainTitle}]`)
                                            await beanHomeIconDoTask({ "flag": "0", "viewChannel": "myjd" })
                                        }
                                        await $.wait(2000)
                                        if (!data.data.viewAppHome.doneTask) {
                                            console.log(`去领奖[${data.data.viewAppHome.mainTitle}]`)
                                            await beanHomeIconDoTask({ "flag": "1", "viewChannel": "AppHome" })
                                        } else {
                                            console.log(`[${data.data.viewAppHome.mainTitle}]已做完`)
                                        }
                                    }
                                    break
                                case 2:
                                    $.doneState = true
                                    let taskInfos = data.data.taskInfos
                                    for (let key of Object.keys(taskInfos)) {
                                        let vo = taskInfos[key]
                                        if (vo.times < vo.maxTimes) {
                                            for (let key of Object.keys(vo.subTaskVOS)) {
                                                let taskList = vo.subTaskVOS[key]
                                                if (taskList.status === 1) {
                                                    $.doneState = false
                                                    console.log(`去做[${vo.taskName}]${taskList.title || ''}`)
                                                    await $.wait(2000)
                                                    await beanDoTask({ "actionType": 1, "taskToken": `${taskList.taskToken}` }, vo.taskType)
                                                    if (vo.taskType === 9 || vo.taskType === 8) {
                                                        await $.wait(vo.waitDuration * 1000 || 5000)
                                                        await beanDoTask({ "actionType": 0, "taskToken": `${taskList.taskToken}` }, vo.taskType)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    break
                                case 3:
                                    let taskInfos3 = data.data.taskInfos
                                    for (let key of Object.keys(taskInfos3)) {
                                        let vo = taskInfos3[key]
                                        if (vo.times === vo.maxTimes) {
                                            console.log(`[${vo.taskName}]已做完`)
                                        }
                                    }
                                default:
                                    break
                            }
                        } else {
                            console.log(data.errorMessage)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}
function beanDoTask(body, taskType) {
    return new Promise(resolve => {
        $.post(taskBeanUrl('beanDoTask', body), (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} beanDoTask API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (body.actionType === 1 && (taskType !== 9 && taskType !== 8)) {
                            if (data.code === "0" && data.data.bizCode === "0") {
                                console.log(`完成任务，获得+${data.data.score}成长值`)
                            } else {
                                console.log(`完成任务失败：${data}`)
                            }
                        }
                        if (body.actionType === 0) {
                            if (data.code === "0" && data.data?.bizCode === "0") {
                                console.log(data.data.bizMsg)
                            } else {
                                console.log(`完成任务失败：${JSON.stringify(data)}`)
                            }
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve(data);
            }
        })
    })
}
function beanHomeIconDoTask(body) {
    return new Promise(resolve => {
        $.post(taskBeanUrl('beanHomeIconDoTask', body), (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} beanHomeIconDoTask API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (body.flag === "0" && data.data.taskResult) {
                            console.log(data.data.remindMsg)
                        }
                        if (body.flag === "1" && data.data.taskResult) {
                            console.log(data.data.remindMsg)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve(data);
            }
        })
    })
}
async function queryCouponInfo() {
    return new Promise(async resolve => {
        $.get(taskBeanUrl('queryCouponInfo', { "rnVersion": "4.7", "fp": "-1", "shshshfp": "-1", "shshshfpa": "-1", "referUrl": "-1", "userAgent": "-1", "jda": "-1" }), async (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} queryCouponInfo API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.data && data.data.couponTaskInfo) {
                            if (!data.data.couponTaskInfo.awardFlag) {
                                console.log(`去做[${data.data.couponTaskInfo.taskName}]`)
                                await sceneGetCoupon()
                            } else {
                                console.log(`[${data.data.couponTaskInfo.taskName}]已做完`)
                            }
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}
function sceneGetCoupon() {
    return new Promise(resolve => {
        $.get(taskBeanUrl('sceneGetCoupon', { "rnVersion": "4.7", "fp": "-1", "shshshfp": "-1", "shshshfpa": "-1", "referUrl": "-1", "userAgent": "-1", "jda": "-1" }), (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} sceneGetCoupon API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.code === '0' && data.data && data.data.bizMsg) {
                            console.log(data.data.bizMsg)
                        } else {
                            console.log(`完成任务失败：${data}`)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}
function randomString() {
    return Math.random().toString(16).slice(2, 10) +
        Math.random().toString(16).slice(2, 10) +
        Math.random().toString(16).slice(2, 10) +
        Math.random().toString(16).slice(2, 10) +
        Math.random().toString(16).slice(2, 10)
}

function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min)) + min;
}
function doTask2() {
    return new Promise(resolve => {
        const body = { "awardFlag": false, "skuId": `${getRandomInt(1000000000, 2000000000)}`, "source": "feeds", "type": '1' };
        $.get(taskGetUrl('beanHomeTask', body), (err, resp, data) => {
            try {
                if (err) {
                    $.flag = false
                    //console.log(`doTask2 API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.code === '0' && data.data) {
                            console.log(`任务完成进度：${data.data.taskProgress}/${data.data.taskThreshold}`)
                            if (data.data.taskProgress === data.data.taskThreshold)
                                $.doneState = true
                        } else if (data.code === '0' && data.errorCode === 'HT201') {
                            $.doneState = true
                        } else {
                            //HT304风控用户
                            $.doneState = true
                            console.log(`做任务异常：${JSON.stringify(data)}`)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}

function getAuthorShareCode(url) {
    return new Promise(resolve => {
        const options = {
            url: `${url}?${new Date()}`, "timeout": 10000, headers: {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/87.0.4280.88"
            }
        };
        if ($.isNode() && process.env.TG_PROXY_HOST && process.env.TG_PROXY_PORT) {
            const tunnel = require("tunnel");
            const agent = {
                https: tunnel.httpsOverHttp({
                    proxy: {
                        host: process.env.TG_PROXY_HOST,
                        port: process.env.TG_PROXY_PORT * 1
                    }
                })
            }
            Object.assign(options, { agent })
        }
        $.get(options, async (err, resp, data) => {
            try {
                if (err) {
                } else {
                    if (data) data = JSON.parse(data)
                }
            } catch (e) {
                // $.logErr(e, resp)
            } finally {
                resolve(data);
            }
        })
    })
}
function getUserInfo() {
    return new Promise(resolve => {
        $.post(taskUrl('signBeanGroupStageIndex', 'body'), async (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.data.jklInfo) {
                            $.actId = data.data.jklInfo.keyId
                            let { shareCode, groupCode } = data.data
                            if (!shareCode) {
                                console.log(`未获取到助力码，去开团`)
                                await hitGroup()
                            } else {
                                console.log(shareCode, groupCode)
                                // 去做逛会场任务
                                if (data.data.beanActivityVisitVenue && data.data.beanActivityVisitVenue.taskStatus === '0') {
                                    await help(shareCode, groupCode, 1)
                                }
                                console.log(`\n京东账号${$.index} ${$.nickName || $.UserName} 抢京豆邀请码：${shareCode}\n`);
                                $.newShareCodes.push([shareCode, groupCode, $.UserName])
                            }
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}

function hitGroup() {
    return new Promise(resolve => {
        const body = { "activeType": 2, };
        $.get(taskGetUrl('signGroupHit', body), async (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.data.respCode === "SG150") {
                            let { shareCode, groupCode } = data.data.signGroupMain
                            if (shareCode) {
                                $.newShareCodes.push([shareCode, groupCode, $.UserName])
                                console.log('开团成功')
                                console.log(`\n京东账号${$.index} ${$.nickName || $.UserName} 抢京豆邀请码：${shareCode}\n`);
                                await help(shareCode, groupCode, 1)
                            } else {
                                console.log(`为获取到助力码，错误信息${JSON.stringify(data.data)}`)
                            }
                        } else {
                            console.log(`开团失败，错误信息${JSON.stringify(data.data)}`)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}

function help(shareCode, groupCode, isTask = 0) {
    return new Promise(resolve => {
        const body = {
            "activeType": 2,
            "groupCode": groupCode,
            "shareCode": shareCode,
            "activeId": $.actId,
        };
        if (isTask) {
            console.log(`【抢京豆】做任务获取助力`)
            body['isTask'] = "1"
        } else {
            console.log(`【抢京豆】去助力好友${shareCode}`)
            body['source'] = "guest"
        }
        $.get(taskGetUrl('signGroupHelp', body), async (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`【抢京豆】${$.name} API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.code === '0') {
                            console.log(`【抢京豆】${data.data.helpToast}`)
                        }
                        if (data.code === '0' && data.data && data.data.respCode === 'SG209') {
                            $.canHelp = false;
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve(data);
            }
        })
    })
}

function showMsg() {
    return new Promise(resolve => {
        if (message) $.msg($.name, '', `【京东账号${$.index}】${$.nickName}\n${message}`);
        resolve()
    })
}

function getTaskList() {
    return new Promise(resolve => {
        const body = { "rnVersion": "4.7", "rnClient": "2", "source": "AppHome" };
        $.post(taskUrl('findBeanHome', body), async (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        let beanTask = data.data.floorList.filter(vo => vo.floorName === "种豆得豆定制化场景")[0]
                        if (!beanTask.viewed) {
                            await receiveTask()
                            await $.wait(3000)
                        }

                        let tasks = data.data.floorList.filter(vo => vo.floorName === "赚京豆")[0]['stageList']
                        for (let i = 0; i < tasks.length; ++i) {
                            const vo = tasks[i]
                            if (vo.viewed) continue
                            await receiveTask(vo.stageId, `4_${vo.stageId}`)
                            await $.wait(3000)
                        }
                        await award()
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}

function receiveTask(itemId = "zddd", type = "3") {
    return new Promise(resolve => {
        const body = { "awardFlag": false, "itemId": itemId, "source": "home", "type": type };
        $.post(taskUrl('beanHomeTask', body), (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`receiveTask API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.data) {
                            console.log(`完成任务成功，进度${data.data.taskProgress}/${data.data.taskThreshold}`)
                        } else {
                            console.log(`完成任务失败，${data.errorMessage}`)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}


function award(source = "home") {
    return new Promise(resolve => {
        const body = { "awardFlag": true, "source": source };
        $.post(taskUrl('beanHomeTask', body), (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`award API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data.data) {
                            console.log(`领奖成功，获得 ${data.data.beanNum} 个京豆`)
                            message += `领奖成功，获得 ${data.data.beanNum} 个京豆\n`
                        } else {
                            console.log(`领奖失败，${data.errorMessage}`)
                            // message += `领奖失败，${data.errorMessage}\n`
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}
function receiveJd2() {
    var headers = {
        'Host': 'api.m.jd.com',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': '*/*',
        'user-agent': 'JD4iPhone/167515 (iPhone; iOS 14.2; Scale/3.00)',
        'accept-language': 'zh-Hans-JP;q=1, en-JP;q=0.9, zh-Hant-TW;q=0.8, ja-JP;q=0.7, en-US;q=0.6',
        'Cookie': cookie
    };
    var dataString = 'body=%7B%7D&build=167576&client=apple&clientVersion=9.4.3&openudid=53f4d9c70c1c81f1c8769d2fe2fef0190a3f60d2&osVersion=14.2&partner=TF&rfs=0000&scope=10&screen=1242%2A2208&sign=19c33b5b9ad4f02c53b6040fc8527119&st=1614701322170&sv=122'
    var options = {
        url: 'https://api.m.jd.com/client.action?functionId=sceneInitialize',
        headers: headers,
        body: dataString
    };
    return new Promise(resolve => {
        $.post(options, (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} API请求失败，请检查网路重试`)
                } else {
                    if (safeGet(data)) {
                        data = JSON.parse(data);
                        if (data['code'] === '0' && data['data']) {
                            console.log(`强制开启新版领京豆成功,获得${data['data']['sceneLevelConfig']['beanNum']}京豆\n`);
                            $.msg($.name, '', `强制开启新版领京豆成功\n获得${data['data']['sceneLevelConfig']['beanNum']}京豆`);
                        } else {
                            console.log(`强制开启新版领京豆结果:${JSON.stringify(data)}\n`)
                        }
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}
function taskGetUrl(function_id, body) {
    return {
        url: `${JD_API_HOST}client.action?functionId=${function_id}&body=${encodeURIComponent(JSON.stringify(body))}&appid=ld&client=android&clientVersion=${$.av}`,
        headers: {
            'Cookie': cookie,
            'Host': 'api.m.jd.com',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'User-Agent': $.UA,
            'Accept-Language': 'zh-Hans-CN;q=1,en-CN;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': "application/x-www-form-urlencoded"
        }
    }
}

function taskBeanUrl(function_id, body = {}) {
    return {
        url: `${JD_API_HOST}client.action?functionId=${function_id}&body=${encodeURIComponent(JSON.stringify(body))}&appid=ld&client=apple&clientVersion=${$.av}&uuid=${uuid}&openudid=${uuid}`,
        headers: {
            'Cookie': cookie,
            'Host': 'api.m.jd.com',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'User-Agent': $.UA,
            'Accept-Language': 'zh-cn',
            'Accept-Encoding': 'gzip, deflate, br',
            "Referer": "https://h5.m.jd.com/"
        }
    }
}

function taskUrl(function_id, body) {
    body["version"] = "9.0.0.1";
    body["monitor_source"] = "plant_app_plant_index";
    body["monitor_refer"] = "";
    return {
        url: JD_API_HOST,
        body: `functionId=${function_id}&body=${encodeURIComponent(JSON.stringify(body))}&appid=ld&client=apple&clientVersion=${$.av}`,
        headers: {
            'Cookie': cookie,
            'Host': 'api.m.jd.com',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'User-Agent': $.UA,
            'Accept-Language': 'zh-Hans-CN;q=1,en-CN;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': "application/x-www-form-urlencoded"
        }
    }
}

function TotalBean() {
    return new Promise(async resolve => {
        const options = {
            "url": `https://wq.jd.com/user/info/QueryJDUserInfo?sceneval=2`,
            "headers": {
                "Accept": "application/json,text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-cn",
                "Connection": "keep-alive",
                "Cookie": cookie,
                "Referer": "https://wqs.jd.com/my/jingdou/my.shtml?sceneval=2",
                "User-Agent": $.isNode() ? (process.env.JD_USER_AGENT ? process.env.JD_USER_AGENT : (require('./USER_AGENTS').USER_AGENT)) : ($.getdata('JDUA') ? $.getdata('JDUA') : "jdapp;iPhone;9.4.4;14.3;network/4g;Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148;supportJDSHWK/1")
            }
        }
        $.post(options, (err, resp, data) => {
            try {
                if (err) {
                    console.log(`${JSON.stringify(err)}`)
                    console.log(`${$.name} API请求失败，请检查网路重试`)
                } else {
                    if (data) {
                        data = JSON.parse(data);
                        if (data['retcode'] === 13) {
                            $.isLogin = false; //cookie过期
                            return
                        }
                        if (data['retcode'] === 0) {
                            $.nickName = (data['base'] && data['base'].nickname) || $.UserName;
                        } else {
                            $.nickName = $.UserName
                        }
                    } else {
                        console.log(`京东服务器返回空数据`)
                    }
                }
            } catch (e) {
                $.logErr(e, resp)
            } finally {
                resolve();
            }
        })
    })
}

function safeGet(data) {
    try {
        if (typeof JSON.parse(data) == "object") {
            return true;
        }
    } catch (e) {
        console.log(e);
        console.log(`京东服务器访问数据为空，请检查自身设备网络情况`);
        return false;
    }
}
function jsonParse(str) {
    if (typeof str == "string") {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.log(e);
            $.msg($.name, '', '请勿随意在BoxJs输入框修改内容\n建议通过脚本去获取cookie')
            return [];
        }
    }
}
// prettier-ignore
function Env(t, e) { "undefined" != typeof process && JSON.stringify(process.env).indexOf("GITHUB") > -1 && process.exit(0); class s { constructor(t) { this.env = t } send(t, e = "GET") { t = "string" == typeof t ? { url: t } : t; let s = this.get; return "POST" === e && (s = this.post), new Promise((e, i) => { s.call(this, t, (t, s, r) => { t ? i(t) : e(s) }) }) } get(t) { return this.send.call(this.env, t) } post(t) { return this.send.call(this.env, t, "POST") } } return new class { constructor(t, e) { this.name = t, this.http = new s(this), this.data = null, this.dataFile = "box.dat", this.logs = [], this.isMute = !1, this.isNeedRewrite = !1, this.logSeparator = "\n", this.startTime = (new Date).getTime(), Object.assign(this, e), this.log("", `🔔${this.name}, 开始!`) } isNode() { return "undefined" != typeof module && !!module.exports } isQuanX() { return "undefined" != typeof $task } isSurge() { return "undefined" != typeof $httpClient && "undefined" == typeof $loon } isLoon() { return "undefined" != typeof $loon } toObj(t, e = null) { try { return JSON.parse(t) } catch { return e } } toStr(t, e = null) { try { return JSON.stringify(t) } catch { return e } } getjson(t, e) { let s = e; const i = this.getdata(t); if (i) try { s = JSON.parse(this.getdata(t)) } catch { } return s } setjson(t, e) { try { return this.setdata(JSON.stringify(t), e) } catch { return !1 } } getScript(t) { return new Promise(e => { this.get({ url: t }, (t, s, i) => e(i)) }) } runScript(t, e) { return new Promise(s => { let i = this.getdata("@chavy_boxjs_userCfgs.httpapi"); i = i ? i.replace(/\n/g, "").trim() : i; let r = this.getdata("@chavy_boxjs_userCfgs.httpapi_timeout"); r = r ? 1 * r : 20, r = e && e.timeout ? e.timeout : r; const [o, h] = i.split("@"), n = { url: `http://${h}/v1/scripting/evaluate`, body: { script_text: t, mock_type: "cron", timeout: r }, headers: { "X-Key": o, Accept: "*/*" } }; this.post(n, (t, e, i) => s(i)) }).catch(t => this.logErr(t)) } loaddata() { if (!this.isNode()) return {}; { this.fs = this.fs ? this.fs : require("fs"), this.path = this.path ? this.path : require("path"); const t = this.path.resolve(this.dataFile), e = this.path.resolve(process.cwd(), this.dataFile), s = this.fs.existsSync(t), i = !s && this.fs.existsSync(e); if (!s && !i) return {}; { const i = s ? t : e; try { return JSON.parse(this.fs.readFileSync(i)) } catch (t) { return {} } } } } writedata() { if (this.isNode()) { this.fs = this.fs ? this.fs : require("fs"), this.path = this.path ? this.path : require("path"); const t = this.path.resolve(this.dataFile), e = this.path.resolve(process.cwd(), this.dataFile), s = this.fs.existsSync(t), i = !s && this.fs.existsSync(e), r = JSON.stringify(this.data); s ? this.fs.writeFileSync(t, r) : i ? this.fs.writeFileSync(e, r) : this.fs.writeFileSync(t, r) } } lodash_get(t, e, s) { const i = e.replace(/\[(\d+)\]/g, ".$1").split("."); let r = t; for (const t of i) if (r = Object(r)[t], void 0 === r) return s; return r } lodash_set(t, e, s) { return Object(t) !== t ? t : (Array.isArray(e) || (e = e.toString().match(/[^.[\]]+/g) || []), e.slice(0, -1).reduce((t, s, i) => Object(t[s]) === t[s] ? t[s] : t[s] = Math.abs(e[i + 1]) >> 0 == +e[i + 1] ? [] : {}, t)[e[e.length - 1]] = s, t) } getdata(t) { let e = this.getval(t); if (/^@/.test(t)) { const [, s, i] = /^@(.*?)\.(.*?)$/.exec(t), r = s ? this.getval(s) : ""; if (r) try { const t = JSON.parse(r); e = t ? this.lodash_get(t, i, "") : e } catch (t) { e = "" } } return e } setdata(t, e) { let s = !1; if (/^@/.test(e)) { const [, i, r] = /^@(.*?)\.(.*?)$/.exec(e), o = this.getval(i), h = i ? "null" === o ? null : o || "{}" : "{}"; try { const e = JSON.parse(h); this.lodash_set(e, r, t), s = this.setval(JSON.stringify(e), i) } catch (e) { const o = {}; this.lodash_set(o, r, t), s = this.setval(JSON.stringify(o), i) } } else s = this.setval(t, e); return s } getval(t) { return this.isSurge() || this.isLoon() ? $persistentStore.read(t) : this.isQuanX() ? $prefs.valueForKey(t) : this.isNode() ? (this.data = this.loaddata(), this.data[t]) : this.data && this.data[t] || null } setval(t, e) { return this.isSurge() || this.isLoon() ? $persistentStore.write(t, e) : this.isQuanX() ? $prefs.setValueForKey(t, e) : this.isNode() ? (this.data = this.loaddata(), this.data[e] = t, this.writedata(), !0) : this.data && this.data[e] || null } initGotEnv(t) { this.got = this.got ? this.got : require("got"), this.cktough = this.cktough ? this.cktough : require("tough-cookie"), this.ckjar = this.ckjar ? this.ckjar : new this.cktough.CookieJar, t && (t.headers = t.headers ? t.headers : {}, void 0 === t.headers.Cookie && void 0 === t.cookieJar && (t.cookieJar = this.ckjar)) } get(t, e = (() => { })) { t.headers && (delete t.headers["Content-Type"], delete t.headers["Content-Length"]), this.isSurge() || this.isLoon() ? (this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, { "X-Surge-Skip-Scripting": !1 })), $httpClient.get(t, (t, s, i) => { !t && s && (s.body = i, s.statusCode = s.status), e(t, s, i) })) : this.isQuanX() ? (this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, { hints: !1 })), $task.fetch(t).then(t => { const { statusCode: s, statusCode: i, headers: r, body: o } = t; e(null, { status: s, statusCode: i, headers: r, body: o }, o) }, t => e(t))) : this.isNode() && (this.initGotEnv(t), this.got(t).on("redirect", (t, e) => { try { if (t.headers["set-cookie"]) { const s = t.headers["set-cookie"].map(this.cktough.Cookie.parse).toString(); s && this.ckjar.setCookieSync(s, null), e.cookieJar = this.ckjar } } catch (t) { this.logErr(t) } }).then(t => { const { statusCode: s, statusCode: i, headers: r, body: o } = t; e(null, { status: s, statusCode: i, headers: r, body: o }, o) }, t => { const { message: s, response: i } = t; e(s, i, i && i.body) })) } post(t, e = (() => { })) { if (t.body && t.headers && !t.headers["Content-Type"] && (t.headers["Content-Type"] = "application/x-www-form-urlencoded"), t.headers && delete t.headers["Content-Length"], this.isSurge() || this.isLoon()) this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, { "X-Surge-Skip-Scripting": !1 })), $httpClient.post(t, (t, s, i) => { !t && s && (s.body = i, s.statusCode = s.status), e(t, s, i) }); else if (this.isQuanX()) t.method = "POST", this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, { hints: !1 })), $task.fetch(t).then(t => { const { statusCode: s, statusCode: i, headers: r, body: o } = t; e(null, { status: s, statusCode: i, headers: r, body: o }, o) }, t => e(t)); else if (this.isNode()) { this.initGotEnv(t); const { url: s, ...i } = t; this.got.post(s, i).then(t => { const { statusCode: s, statusCode: i, headers: r, body: o } = t; e(null, { status: s, statusCode: i, headers: r, body: o }, o) }, t => { const { message: s, response: i } = t; e(s, i, i && i.body) }) } } time(t, e = null) { const s = e ? new Date(e) : new Date; let i = { "M+": s.getMonth() + 1, "d+": s.getDate(), "H+": s.getHours(), "m+": s.getMinutes(), "s+": s.getSeconds(), "q+": Math.floor((s.getMonth() + 3) / 3), S: s.getMilliseconds() }; /(y+)/.test(t) && (t = t.replace(RegExp.$1, (s.getFullYear() + "").substr(4 - RegExp.$1.length))); for (let e in i) new RegExp("(" + e + ")").test(t) && (t = t.replace(RegExp.$1, 1 == RegExp.$1.length ? i[e] : ("00" + i[e]).substr(("" + i[e]).length))); return t } msg(e = t, s = "", i = "", r) { const o = t => { if (!t) return t; if ("string" == typeof t) return this.isLoon() ? t : this.isQuanX() ? { "open-url": t } : this.isSurge() ? { url: t } : void 0; if ("object" == typeof t) { if (this.isLoon()) { let e = t.openUrl || t.url || t["open-url"], s = t.mediaUrl || t["media-url"]; return { openUrl: e, mediaUrl: s } } if (this.isQuanX()) { let e = t["open-url"] || t.url || t.openUrl, s = t["media-url"] || t.mediaUrl; return { "open-url": e, "media-url": s } } if (this.isSurge()) { let e = t.url || t.openUrl || t["open-url"]; return { url: e } } } }; if (this.isMute || (this.isSurge() || this.isLoon() ? $notification.post(e, s, i, o(r)) : this.isQuanX() && $notify(e, s, i, o(r))), !this.isMuteLog) { let t = ["", "==============📣系统通知📣=============="]; t.push(e), s && t.push(s), i && t.push(i), console.log(t.join("\n")), this.logs = this.logs.concat(t) } } log(...t) { t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(t.join(this.logSeparator)) } logErr(t, e) { const s = !this.isSurge() && !this.isQuanX() && !this.isLoon(); s ? this.log("", `❗️${this.name}, 错误!`, t.stack) : this.log("", `❗️${this.name}, 错误!`, t) } wait(t) { return new Promise(e => setTimeout(e, t)) } done(t = {}) { const e = (new Date).getTime(), s = (e - this.startTime) / 1e3; this.log("", `🔔${this.name}, 结束! 🕛 ${s} 秒`), this.log(), (this.isSurge() || this.isQuanX() || this.isLoon()) && $done(t) } }(t, e) }