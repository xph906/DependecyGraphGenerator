@load base/utils/site
@load base/frameworks/notice
@load base/protocols/http
@load base/protocols/ssl
@load policy/protocols/http/detect-sqli.bro
@load base/protocols/conn
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

event http_reply(c: connection, version: string, code: count, reason: string) &priority=0
{
	print fmt("{\"TAG\":\"RESPB\", \"TIME\":%f, \"DSTIP\":\"%-15s\", \"URL\":\"http://%s%s\"}",network_time(),c$http$id$resp_h,c$http$host,c$http$uri);
}

#event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string){
event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string) &priority=0
{
	#print "sdsd";
	c$http$uri = gsub(original_URI,/\'|\"/,"-");
	#print fmt("[%f] REQUEST: %s/%s",network_time(), c$http$host,original_URI);
}
	
event http_header(c: connection, is_orig: bool, name: string, value: string) &priority=0
{
	if ( is_orig ) # client headers
	{
		if ( name == "HOST" ){
			if(c$http?$host){
				print fmt("{\"TAG\":\"REQ\",   \"TIME\":%f, \"DSTIP\":\"%-15s\", \"URL\":\"http://%s%s\"}",network_time(),c$http$id$resp_h,c$http$host,c$http$uri);
			}
		}
	}
}

event SSL::log_ssl(rec: SSL::Info)
{
	print fmt("{\"TAG\":\"REQ\",   \"TIME\":%f, \"DSTIP\":\"%-15s\", \"URL\":\"https://%s\"}",network_time(),rec$id$resp_h,rec$server_name);
}	

event http_message_done(c: connection, is_orig: bool, stat: http_message_stat) &priority=0
{
	if(is_orig==F )	{
		if(c$http?$host)
			print fmt("{\"TAG\":\"RESPD\", \"TIME\":%f, \"DSTIP\":\"%-15s\", \"URL\":\"http://%s%s\", \"SIZE\":%d}",
					network_time(),c$http$id$resp_h,c$http$host,c$http$uri,c$http$response_body_len);
		else
			print fmt("NOHOST:%s",c$http$uri);
	}
		
}

event connection_established(c: connection)  &priority=0
{
	print fmt("{\"TAG\":\"CONNE\", \"TIME\":%f, \"DSTIP\":\"%-15s\", \"DSTPORT\":%d, \"DURATION\":%f, \"SRCPORT\":%d}",network_time(), c$id$resp_h, port_to_count(c$id$resp_p),c$duration,port_to_count(c$id$orig_p) );
}



#event connection_SYN_packet(c: connection, pkt: SYN_packet) &priority=0
#{
#	print fmt("NEW_C TIME:%f DSTIP:%s DSTPORT:%d SRCPORT:%d",network_time(), c$id$resp_h, port_to_count(c$id$resp_p),port_to_count(c$id$orig_p) );
#}