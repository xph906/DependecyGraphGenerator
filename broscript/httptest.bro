@load base/utils/site
@load base/frameworks/notice
@load base/protocols/http
@load policy/protocols/http/detect-sqli.bro
redef Site::local_nets += { 10.2.0.0/16, 165.124.182.177/32 };
module HTTP;

export {

	global success_status_codes: set[count] = {
		200,
		201,
		202,
		203,
		204,
		205,
		206,
		207,
		208,
		226,
		304
	};
}




event http_reply(c: connection, version: string, code: count, reason: string)
{
	
	#print fmt("[%s] REPLY: %s",strftime("%Y/%M/%d %H:%m:%S", network_time()), c$http$uri);
}

#event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string){
event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)&priority=10
{
	print "sdsd";
	c$http$uri = original_URI;
	print fmt("[%s] REQUEST: %s",strftime("%Y/%M/%d %H:%m:%S", network_time()), original_URI);
}
	
event http_request(c: connection, method: string, original_URI: string,
                   unescaped_URI: string, version: string) &priority=5
	{
	print "sddd";
}
event http_message_done(c: connection, is_orig: bool, stat: http_message_stat){
	#if(is_orig==F )
		#print fmt("[%s] REPLY_MSG_DONE: %s",strftime("%Y/%M/%d %H:%m:%S", network_time()), c$http$uri);
}