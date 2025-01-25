import os
import re
import pandas as pd
from tabulate import tabulate
#version 1
# change1
# Specify the file name this will be an environment variable later 
file_name = "IKE_Log_cert_auth_fail.txt"
# IKE_Log_cert_auth_fail
# IKE_Log_cert_auth.txt
# IKE_LOG_V1_radius_username_wrong_v2.txt
# IKE_LOG_V1_radius_DNS_Issues.txt
# IKE_LOG_V1_radius_not_reachable.txt
# IKE_LOG_V1_radius_wrong_account.txt
# IKE_LOG_V1_radius_pswd_wrong
# IKE_LOG_V1_radius_succes
# IKE_LOG_DH_grouo_known_issue
# IKE_LOG_V1_ldap_PSK_Mismatch.txt\
# IKE_LOG_V1_ldap_non_reachable_2
# IKE_LOG_V1_ldap_non_reachable_1
# IKE_LOG_V1_ldap_non_working_pswd_2
# IKE_LOG_V1_ldap_non_working_pswd_1
# IKE_LOG_V1_ldap_working.txt
# IKE_LOG_V1_local_pwd_non_working_2
# IKE_LOG_V1_local_pwd_working.txt
# IKE_LOG_V1_local_pwd_non_working_1
# IKE_LOG_pwd_radius_auth_cert
# IKE_LOG_pwd_radius_auth_fail.txt
# IKE_LOG_pwd_radius_auth.txt
# IKE_LOG_pwd_psk_mismatch.txt
# IKE_LOG_pwd_mismatch.txt
# IKE_LOG_V2_PSK.txt
# IKE_LOG_V2_Mismatch.txt
# IKE_SAMPLE_LOG.txt
# IKE_LOG_V2
# IKE_LOG_PFS_mismatch.txt
# IKE_LOG_V2_Partial_selector.txt
# IKE_LOG_V2_ph_2_TS_mismatch_responder.txt
# IKE_LOG_V2_ph_2_TS_mismatch_initiator.txt
# IKE_Log_combined_all.txt
# IKE_LOG_retrans
# array to store sentencs to display to the user
# IKE_LOG_V2_multiple_phase_2
# IKE_LOG_V2_multiple_phase_2_initiator.txt
# IKE_LOG_V2_policy_not_found
# IKE_LOG_passive_mode
# mani_sir_log
# IKE_LOG_V2_4500_initiator
# IKE_LOG_V2_4500_responder
# IKE_LOG_V2_rekey
# IKE_LOG_V2_net_un
# IKE_LOG_peer_id
# IKE_LOG_auth_response
# IKE_LOG_init_no_policy
# IKE_LOG_V2_overlay_2_init
# ike_fnbamd_local.txt
# IKE_LOG_V1_radius_password_wrong_v2.txt

analysis_output = []

def read_file(filename):
    # Get the directory of the current script
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the full file path
    file_path = os.path.join(current_directory, filename)
    
    try:
        # Open and read the file
        with open(file_path, 'r') as file:
            content = file.read()
            return str(content)
    except FileNotFoundError:
        print(f"The file '{filename}' was not found in the current directory.")
    except Exception as e:
        print(f"An error occurred: {e}")

def ike_parser(text):
    """
    Finds and prints lines containing the phrase 'SA proposal chosen' in the given text.

    :param text: The multi-line string to search through.
    """
    comes_line_phase_1 = None
    ike_phase_1_type = None
    comes_line = None
    NETWORK_ID=''
    fail_line = None
    lines = text.splitlines()
    connection_info_retrans = None
    timeout_index = -1
    src_pattern = r"src .*?:([\d.]+-[\d.]+)"
    dst_pattern = r"dst .*?:([\d.]+-[\d.]+)"
    src_pattern_mis = r"TSi_0\s\d+:[\d.]+-[\d.]+:\d+"
    dst_pattern_mis = r"TSr_0\s\d+:[\d.]+-[\d.]+:\d+"
    src_selectors = None
    dst_selectors = None
    policy_error = False
    src=''
    dst=''
    src_mis=''
    dst_mis=''
    RED = '\033[91m'
    RESET = '\033[0m'
    passive_mode_pattern = r"ignoring request to establish IPsec SA, gateway is in passive mode"
    connection_pattern = r"IPsec SA connect \d+ (\d+\.\d+\.\d+\.\d+->\d+\.\d+\.\d+\.\d+:\d+)"
    for i, line in enumerate(lines):

        # Phase-1 check
        if "SA proposal chosen" in line and "no SA proposal chosen" not in line:
            _phase_1_check(i,line,lines,comes_line_phase_1)
            comes_line_phase_1 = None
        
        # Phase-2 selector object storage
        if re.search(src_pattern, line):
            src = re.search(src_pattern, line).group(1)
        if re.search(src_pattern_mis, line):
            src_mis = re.search(src_pattern_mis, line).group(0)
         
        # Phase-2 selector object storage    
        if re.search(dst_pattern, line):
            dst = re.search(dst_pattern, line).group(1)
        if re.search(dst_pattern_mis, line):
            dst_mis = re.search(dst_pattern_mis, line).group(0)

        if 'processing notify type NO_PROPOSAL_CHOSEN' in line:
            _notify_no_proposal_chosen(i,line,comes_line_phase_1)
            comes_line_phase_1 = None 

        # phase-2 check    
        if "added IPsec SA" in line:
            selectors = ''
            if src and dst:
                selectors = f'[{str(i+1)}]:: The selectors are: \n'+'src: '+src+'\n'+'dst: '+dst             
            _phase_2_check(i,line,lines,comes_line_phase_1,selectors)    
            comes_line_phase_1 = None    
            src_selectors = None
            dst_selectors = None
        
        #Flagging for no policy configured

        if 'no policy configured' in line and 'ignoring request to establish IPsec SA' in line:
            ipsec_lines = lines[-10:]
            ipsec_sa_pattern = re.compile(r"IPsec SA connect .* (\d+\.\d+\.\d+\.\d+->\d+\.\d+\.\d+\.\d+:\d+)")
            ipsec_connections = [match.group(1) for line in ipsec_lines if (match := ipsec_sa_pattern.search(line))]
            analysis_output.append(f'[{str(i+1)}]:: No Policy found for connection as: {list(set(ipsec_connections))[0]}')

        if 'no policy configured' in line and 'ignoring request to establish IPsec SA' not in line:
            _no_policy_configured(i,comes_line_phase_1)
            policy_error = True
            comes_line_phase_1 = None
        
        if "gw validation failed" in line:
            print('BINGO')
            last_10_lines = []
            start_index = max(i - 10, 0) 
            last_10_lines.append(line)
            for j in range(start_index, i):
                last_10_lines.append(lines[j])

            # Check if "FQDN 'admin'" is in any of the last 10 lines
            if any("received peer identifier" in log for log in last_10_lines):
                _peer_id_fail(i,line,comes_line_phase_1,ike_phase_1_type)
                comes_line_phase_1 = None
                ike_phase_1_type = None
                comes_line = None
                fail_line = None
            else:
                if comes_line_phase_1:
                    _gw_validation_fail(i,line,comes_line_phase_1,ike_phase_1_type)
                    comes_line_phase_1 = None
                    ike_phase_1_type = None
                    comes_line = None
                    fail_line = None

        if "VPN_NETWORK_ID" in line:
            # Check up to 5 lines below the matched line
            for j in range(i + 1, min(i + 6, len(lines))):
                if "NETWORK ID :" in lines[j]:
                    # Extract the number after "NETWORK ID :"
                    parts = lines[j].split(":")
                    if len(parts) > 1:
                        try:
                            NETWORK_ID=' Network ID mismatch with value '+parts[-1]
                        except ValueError:
                            pass  # Ignore lines that don't have a valid number

        #Check for Phase-1 Negotiation failures
        if "negotiation failure" in line or "no proposal chosen" in line:
            fail_line=i
            if comes_line_phase_1 and policy_error == False:
                Ike_param = _extract_lines(lines, comes_line, fail_line)
                _phase_1_2_mismatch(i,line,comes_line_phase_1,ike_phase_1_type,Ike_param,NETWORK_ID)
                comes_line_phase_1 = None
                ike_phase_1_type = None
                comes_line = None
                fail_line = None
                NETWORK_ID=''
            else:
                policy_error = False

        
        if "PSK auth failed: probable pre-shared key mismatch" in line:
            if comes_line_phase_1:
                _phase_1_psk_fail(i,line,comes_line_phase_1,ike_phase_1_type)
                comes_line_phase_1 = None
                ike_phase_1_type = None
                comes_line = None
                fail_line = None
        
        # Grabs the connection details for the phase-1 mismatch
        if "comes" in line:
            comes_line_phase_1 = line
            comes_line = i + 3
            if i + 1 < len(lines):
                ike_phase_1_type = lines[i + 1]

            # _phase_1_mismatch_V1(i,line,lines)
        
        if "matched by intersection" in line:
            selectors = ''
            if src and dst:
                selectors = f'[{str(i+1)}]:: The selectors are: \n'+'src: '+src+'\n'+'dst: '+dst 
            _phase_2_subset(i,line,lines,selectors)

        if "failed to match peer selectors" in line:
            fail_line=i
            selectors = ''
            if comes_line_phase_1:
                if src_mis and dst_mis:
                    selectors = f'[{str(i+1)}]:: The selectors are: \n'+'src: '+src_mis+'\n'+'dst: '+dst_mis 
                _phase_2_ts_mismatch_responder(i,line,lines,comes_line_phase_1,ike_phase_1_type,selectors)
                comes_line_phase_1 = None
                ike_phase_1_type = None
                comes_line = None
                fail_line = None
                src_selectors = None
                dst_selectors = None
        
        if 'TS_UNACCEPTABLE' in line:
            fail_line=i
            if comes_line_phase_1:
                _phase_2_ts_mismatch_initiator(i,line,lines,comes_line_phase_1,ike_phase_1_type)
                comes_line_phase_1 = None
                ike_phase_1_type = None
                comes_line = None
                fail_line = None

        if "connection expiring due to phase1 down" in line and timeout_index == -1:
            _phase_1_retrans_check_1(line,lines,i)
        if "connection expiring due to phase1 down" in line and timeout_index != -1:
            if comes_line_phase_1:
                start_index_failure = comes_line_phase_1.index("comes")
                failure_message = comes_line_phase_1[start_index_failure:]
                for prev_line in lines[:i]:
                    if "EAP identity request" in prev_line:
                        analysis_output.append(f'<span style="color: red;">[{str(i+1)}]::VPN with IP Connection as:: '+failure_message+' is down due to bad PSK in EAP Request from clinet </span>')

        if "negotiation timeout, deleting" in line:
            timeout_index = i
        
        if timeout_index != -1 and abs(i - timeout_index) <= 5:
            print('hit the old con exp')
            if "connection expiring due to phase1 down" in line:
                # Search for the connection info pattern in the log
                _phase_1_retrans_check_1(line,lines,i)
                timeout_index = -1
        
        #No Policy found use case
        if re.search(passive_mode_pattern, line):
            # Look ahead to find connection details in the next lines
            for j in range(i + 1, len(lines)):
                match = re.search(connection_pattern, lines[j])
                if match:
                    analysis_output.append(f'[{str(i+1)}]:: Gateway in passive mode for connection: '+match.group(1))
                    break
        
        # Check for rekey of phaase-2
        if "rekey" in line:
            # Extract the connection information using string manipulation
            parts = line.split()
            for part in parts:
                if "->" in part and ":" in part:
                    analysis_output.append(f'[{str(i+1)}]:: Rekey connection found: {part}')
                    break
        # Rekey failures catch
        if 'rekey in progress' in line:
            retransmit_count = 0
            for j in range(i + 1, min(i + 150, len(lines))):
                if 'RETRANSMIT_CREATE_CHILD' in lines[j]:
                    retransmit_count += 1
                if retransmit_count >= 3:
                    analysis_output.append(f'[{str(i+1)}]:: rekey in progress followed by 3 RETRANSMIT_CREATE_CHILD. Possible re-key failures')

        
        # Check for keepalives
        if 'keepalive' in line:
            # Extract the IP address from the line
            parts = line.split()
            for part in parts:
                if '->' in part:
                    connection_ip = part.split('->')[1].split(':')[0]
                    break
            else:
                continue

            # Count 'keepalive' occurrences in the next 25 lines
            keepalive_count = sum(1 for l in lines[i:i + 25] if 'keepalive' in l)

            # Check if it meets the condition
            if keepalive_count >= 5:
                analysis_output.append(f'[{str(i+1)}]:: 5 consecutive keep-alives detected for connection: {part}. Check: \n-> ISP issues \n->re-key issues \n-> Check if peer is Meraki')

        # Check for network unreachable
        if "Network is unreachable" in line:
            # Use regex to extract the IP connection details
            match = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+->\d+\.\d+\.\d+\.\d+:\d+)", line)
            if match:
                analysis_output.append(f'[{str(i+1)}]:: Network Unreachable for connection: {match.group(1)} Check: \n->Next hop IP \n->Route to the peer \n->Arp of next hop')

#IKE v1 auth logic
        if 'ike' in line and 'sending XAUTH request' in line:
            context = lines[i:i + 150]
            user, group, eap_id = None, None, None
            for entry in context:
                if 'XAUTH user' in entry:
                    user = entry.split('"')[1]  # Extract "vpnuser"
                if 'auth group' in entry:
                    group = entry.split()[-1]  # Extract "local-users"
                if 'XAUTH' in entry and 'pending' in entry and 'ike' in entry:
                    match = re.search(r"XAUTH (\d+)", entry)
                    if match:
                        eap_id = match.group(1)
            if user and group==None  and eap_id==None:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: {user} group: Unknown   Fnbamd-ID: Unknown')
            if user and group  and eap_id:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: {user} group: {group}   Fnbamd-ID: {eap_id}')
            if user and eap_id:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: {user} group: Unknown   Fnbamd-ID: {eap_id}')
            if group  and eap_id:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: Unknown group: {group}   Fnbamd-ID: {eap_id}')                            
            if eap_id:
                rest_lines = lines[i:]
                for k,remaining_line in enumerate(rest_lines):
                    
                    if eap_id in remaining_line:
                        analysis_output.append(f'   [{str(i+k+1)}]{remaining_line.strip()}')
                    if eap_id in remaining_line and "FNBAM_DENIED" in remaining_line:
                        last_10_lines = rest_lines[max(0, k - 9):k + 1]
                        if any("find_matched_usr_grps-Failed group matching" in l for l in last_10_lines):
                            analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] Fnbamd failing due to possible group mismatch</span>')
                    if 'fnbam_user_auth_group_match' in remaining_line and eap_id in remaining_line:
                            analysis_output.append(f'<span style="color: yellow;">[{str(i+k+1)}] Check the server response in the above line</span>')
                    if 'fnbamd_comm_send_result' in remaining_line and eap_id in remaining_line:
                        match = re.search(r"Sending result (\d+)", remaining_line)
                        if match:
                            result_value = int(match.group(1))
                            if result_value == 0:
                                analysis_output.append(f'<span style="color: green;">[{str(i+k+1)}] fnbamd success for the above connection </span>')
                            if result_value == 1:
                                analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] fnbamd deny for the above connection </span>')
                            if result_value == 2:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] fnbamd Challenge for the above connection </span>')
                            if result_value == 5:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] fnbamd ERROR for the above connection </span>')
                        else:
                            analysis_output.append(f'<span style="color: yellow;">[{str(i+k+1)}] Check the Fnbam result in the above line \n 0-->SUCCESS 1---> DENY 2--> CHALLENGE</span>')
                    if eap_id in remaining_line and 'result' in remaining_line:
                        context = rest_lines[k:k + 7]
                        for info in context:
                            if 'XAUTH' in info and 'result' not in info:
                                analysis_output.append(f'       [{str(i+k+1)}]{info.strip()}')
                    if eap_id in remaining_line and 'FNBAM_DENIED' in remaining_line:
                        for prev_line in reversed(rest_lines[:k]):
                            if "ldap_next_state" in prev_line and 'ldap_next_state-State' not in prev_line:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] LDAP log found for deny. Could be a possible reason as: {prev_line}</span>')
                            if "fnbamd_ldap_parse_response-Error" in prev_line:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] LDAP log found for deny. Could be a possible reason as: {prev_line}</span>')
                    if eap_id in remaining_line and 'FNBAM_ERROR' in remaining_line:
                        analysis_output.append(f'<span style="color: yellow;">[{str(i+k+1)}] FNBAMD ERROR means possible FNBAMD Unavailaibility due to lack of servers or non_reachability or DNS issues</span>')
                        for prev_line in reversed(rest_lines[:k]):
                            if "__ldap_try_next_server-No more server to try." in prev_line:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] LDAP log found for FNBAM_error. Could be a possible reason as: {prev_line}</span>')
                            if "fnbamd_dns_parse_resp" in prev_line and 'wrong dns format' in prev_line:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] LDAP log found for deny. DNS for LDAP server issue detected</span>')
                    if eap_id in remaining_line and 'FNBAM_TIMEOUT' in remaining_line:
                        analysis_output.append(f'<span style="color: yellow;">[{str(i+k+1)}] FNBAM_TIMEOUT means possible FNBAMD Unavailaibility due to lack of servers or non_reachability or retries exceeded for wrong credentials</span>')
                        for prev_line in reversed(rest_lines[:k]):
                            if "__ldap_try_next_server-No more server to try." in prev_line:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] LDAP log found for FNBAM_error. Could be a possible reason as: {prev_line}</span>')
                            if "fnbamd_cfg_ldap_update_reachability" in prev_line and 'conn_fails' in prev_line:
                                analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] LDAP log found for deny. SERVER not reachable as in log {prev_line}</span>')
                    # RADIUS LOGIC 
                    if eap_id in remaining_line and 'fnbamd_rad_process-Result' in remaining_line:
                        proceed = True
                        match1 = re.search(r"svr\s'([^']+)'", remaining_line)
                        if match1:
                            svr = match1.group(1)  # Extracts 'EAP_PROXY'
                            print(svr)
                            for prev_line in reversed(rest_lines[:k]):
                                if "fnbamd_cfg_radius_update_reachability" in prev_line and 'conn_fails' in prev_line and svr in prev_line:
                                    analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] RADIUS log found for deny. SERVER not reachable as in log {prev_line}</span>')
                                if "__rad_try_next_server-No more server to try." in prev_line:
                                    analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] RADIUS log found for FNBAM_error. Could be a possible reason as: {prev_line}</span>')
                                if "__fnbamd_rad_dns_cb-Resolved" in prev_line and '0.0.0.0' in prev_line and svr in prev_line:
                                    analysis_output.append(f'<span style="color: orange;">[{str(i+k+1)}] RADIUS reason for deny found. DNS for RADIUS server issue detected</span>') 
                                    proceed = False
                        pattern = r"Result from radius svr '.*?' is (\d+)"
                        match = re.search(pattern, remaining_line)
                        if match and proceed == True:
                            if int(match.group(1)) == 10:
                                analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] radius issue detected for wrong username or password by USER: {user} </span>')
                            if int(match.group(1)) == 1:
                                analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] radius issue detected for wrong password by USER: {user} </span>')


#IKE v2 auth logic
        if 'ike' in line and 'send EAP message to FNBAM' in line:
            context = lines[i:i + 150]
            user, group, eap_id = None, None, None
            for entry in context:
                if 'EAP user' in entry:
                    user = entry.split('"')[1]  # Extract "vpnuser"
                if 'auth group' in entry:
                    group = entry.split()[-1]  # Extract "local-users"
                if 'EAP' in entry and 'pending' in entry and 'ike' in entry:
                    match = re.search(r"EAP (\d+)", entry)
                    if match:
                        eap_id = match.group(1)
            if user and group==None  and eap_id==None:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: {user} group: Unknown   Fnbamd-ID: Unknown')
            if user and group  and eap_id:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: {user} group: {group}   Fnbamd-ID: {eap_id}')
            if user and eap_id:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: {user} group: Unknown   Fnbamd-ID: {eap_id}')
            if group  and eap_id:
                analysis_output.append(f'   The auth log anlysis for the above connection \n    user: Unknown group: {group}   Fnbamd-ID: {eap_id}')                            
            print(user)
            if eap_id:
                rest_lines = lines[i:]
                for k,remaining_line in enumerate(rest_lines):
                    
                    if eap_id in remaining_line:
                        analysis_output.append(f'   [{str(i+k+1)}]{remaining_line.strip()}')
                    if eap_id in remaining_line and "FNBAM_DENIED" in remaining_line:
                        last_10_lines = rest_lines[max(0, k - 9):k + 1]
                        if any("find_matched_usr_grps-Failed group matching" in l for l in last_10_lines):
                            analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] Fnbamd failing due to possible group mismatch</span>')
                    if 'fnbamd_rad_process-Result' in remaining_line:
                        pattern = r"svr\s'([^']+)'\s.*?is\s(\d+)"
                        match = re.search(pattern, remaining_line)
                        if match:
                            svr = match.group(1)  # Extracts 'EAP_PROXY'
                            code = match.group(2)  # Extracts '1'
                            if svr == 'EAP_PROXY':
                                result = ''
                                if code == '1':
                                    result = 'denied'
                                if code == '0':
                                    result = 'success'
                                if code == '2':
                                    result = 'Challenged or still in progress or need more info'
                                analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] Trying Local authentication with local-user and the current status is {result}</span>')
                            else:
                                if code == '1':
                                    result = 'denied'
                                if code == '0':
                                    result = 'success'
                                if code == '2':
                                    result = 'Challenged or still in progress or need more info'
                                analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] Trying radius authentication and the current status as {result}</span>')

                        else:
                            analysis_output.append(f'<span style="color: red;">[{str(i+k+1)}] Check the server response in the above line</span>')
                    if eap_id in remaining_line and 'result' in remaining_line:
                        context = rest_lines[k:k + 7]
                        for info in context:
                            if 'EAP' in info and 'result' not in info:
                                analysis_output.append(f'       [{str(i+k+1)}]{info.strip()}')
# Adding known issue
        if 'compute DH shared secret request queued' in line:
            pattern = "compute DH shared secret request queued"
            count = 1

            # Check the next 20 lines for additional matches
            for j in range(1, 21):
                if i + j < len(lines) and re.search(pattern, lines[i + j]):
                    count += 1
            if count >= 10:
                analysis_output.append(f'<span style="color: red;">Known Issue detected \n Please check: https://community.fortinet.com/t5/FortiClient/Troubleshooting-Tip-Dial-up-IPsec-VPN-in-aggressive-mode-when/ta-p/189924</span>')

# CERT AUTH LOGIC
        if 'ike' in line and 'received peer identifier' in line:
            match = re.search(r"received peer identifier (.+)", line)
            if match:
                peer_identifier = match.group(1)
                analysis_output.append(f'[{str(i+1)}]<span style="color: yellow;">Cert auth detected as : {peer_identifier}</span>')
            else:
                analysis_output.append(f'<span style="color: yellow;">Cert auth detected at line [{str(i+1)}]</span>')
            
        if 'ike' in line and 'peer cert' in line:
            match = re.search(r"subject='([^']+)', issuer='([^']+)'", line)
            if match:
                subject = match.group(1)
                issuer = match.group(2)
                analysis_output.append(f'<span style="color: yellow;">Peer cert as :</span> \nSubject: {subject} \nIssuer: {issuer}')
        if 'ike' in line and 'peer CA cert' in line:
            match = re.search(r"subject='([^']+)', issuer='([^']+)'", line)
            if match:
                subject = match.group(1)
                issuer = match.group(2)
                print(f"Subject: {subject}")
                print(f"Issuer: {issuer}")
                analysis_output.append(f'<span style="color: yellow;">Peer CA cert :</span> \nSubject: {subject} \nIssuer: {issuer}')
        if 'ike' in line and 'signature verification succeeded' in line:
            analysis_output.append(f'<span style="color: green;">[{str(i+1)}]Cert auth succeeded')
        if 'ike' in line and 'certificate validation failed' in line:
            analysis_output.append(f'<span style="color: red;">[{str(i+1)}]IKE connection down due to Cert auth fail')
            analysis_output.append(f'<span style="color: yellow;">Please Check:\n CA signed bt valid CA or the root CA istalled in FGT \n Bad PKI user \n Re-check cert auth settings: {issuer} ')

def _extract_lines(lines, start_line, end_line):
    input_string = "\n".join(lines[start_line-1:end_line])
    split_keyword = "my proposal"
    split_index = input_string.find(split_keyword)
    
    # Split the string into two parts
    if split_index != -1:
        part1 = input_string[:split_index].strip()
        part2 = input_string[split_index:].strip()
        return [part1, part2]
    else:
        return None, None



# Phase-1 check helper function
def _phase_1_check(i,line,lines,comes_line_phase_1):
    start_index = line.index("SA proposal chosen")
    sa_proposal = line[start_index:]
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    # Also get the connection for which SA proposal is chosen
    analysis_output.append(f'[{str(i+1)}]::'+sa_proposal+' VPN with IP Connection as:'+failure_message+' is UP for phase-1')

# Phase-2 check helper function
def _phase_2_check(i,line,lines,comes_line_phase_1,selectors):
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    analysis_output.append(f'[{str(i+1)}]::'+'VPN with IP Connection as -> '+failure_message+' is UP for phase-2 \n'+selectors)

# Phase-1/2 mismatch helper function
def _phase_1_2_mismatch(i,line,comes_line_phase_1,ike_phase_1_type,Ike_param,NETWORK_ID):
    Ike_type = ''
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    mismatch_param = ''    
    phase_2=False
    def compare_ike_proposals(string1, string2):
        param = []
        # Regular expression to extract the relevant IKE parameters
        pattern = r"type=([A-Z_]+),\s*val=([A-Za-z0-9_]+)(?:,\s*key-len=(\d+))?"

        # Extract the parameters from both strings
        def extract_parameters(s):
            # Clean up extra whitespace and capture parameters
            return re.findall(pattern, s.replace("\n", " ").replace("\r", " ").strip())

        params1 = extract_parameters(string1)
        params2 = extract_parameters(string2)

        mismatched_params = []

        # Compare parameters
        for p1, p2 in zip(params1, params2):
            if p1 != p2:
                mismatched_params.append((p1, p2))

        if mismatched_params:
            for p1, p2 in mismatched_params:
                # print(f"Parameter 1: {p1} | Parameter 2: {p2}")
                param.append(f"Incoming: {p1} | local: {p2}")
        return " ,, ".join(param)
    
    # Statement to check for phase-1 mismatch and also for phase-2 diff
    if Ike_param[0] is not None and Ike_param[1] is not None:
        mismatch_param = compare_ike_proposals(Ike_param[0], Ike_param[1])
        
        # check pfs disable on remote peer 
        if ("PFS is disabled" in Ike_param[0] and "PFS is disabled" not in Ike_param[1]):
            if "IKEv1" in ike_phase_1_type:
                Ike_type = "IKE-V1"
                analysis_output.append(f'[{str(i+1)}]::'+' Negotiation Failure for '+f'{Ike_type}'+ ' Phase-2 connection '+failure_message.split()[1]+' due to PFS being disabled in remote peer')
            if "IKEv2" in ike_phase_1_type:
                Ike_type = "IKE-V2"
                analysis_output.append(f'[{str(i+1)}]::'+' Negotiation Failure for '+f'{Ike_type}'+ ' Phase-2 connection '+failure_message.split()[1]+' due to PFS being disabled in remote peer')
            # turn on phase_2 flag
            phase_2=True
            
        # check pfs disable on local peer 
        if ("PFS is disabled" in Ike_param[1] and "PFS is disabled" not in Ike_param[0]):
            if "IKEv1" in ike_phase_1_type:
                Ike_type = "IKE-V1"
                analysis_output.append(f'[{str(i+1)}]::'+' Negotiation Failure for '+f'{Ike_type}'+ ' Phase-2 connection '+failure_message.split()[1]+' due to PFS being disabled in local peer')
            if "IKEv2" in ike_phase_1_type:
                Ike_type = "IKE-V2"
                analysis_output.append(f'[{str(i+1)}]::'+' Negotiation Failure for '+f'{Ike_type}'+ ' Phase-2 connection '+failure_message.split()[1]+' due to PFS being disabled in local peer')
            # turn on phase_2 flag
            phase_2=True
    
    # only hit this statement if phase_2 remains false
    if "IKEv1" in ike_phase_1_type and phase_2==False:
        Ike_type = "IKE-V1"
        analysis_output.append(f'[{str(i+1)}]::'+' Negotiation Failure for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' With mismatch as'+NETWORK_ID+'\n'+str(parse_to_table(mismatch_param)))

    # only hit this statement if phase_2 remains false
    if "IKEv2" in ike_phase_1_type and phase_2==False:
        Ike_type = "IKE-V2"
        analysis_output.append(f'[{str(i+1)}]::'+' Negotiation Failure for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' With mismatch as'+NETWORK_ID+'\n'+str(parse_to_table(mismatch_param)))


def _phase_1_psk_fail(i,line,comes_line_phase_1,ike_phase_1_type):
    Ike_type = ''
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    if "IKEv1" in ike_phase_1_type:
        Ike_type = "IKE-V1"
        analysis_output.append(f'[{str(i+1)}]::'+' PSK Mismatch for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' Please check PSK ')
    if "IKEv2" in ike_phase_1_type:
        Ike_type = "IKE-V2"
        analysis_output.append(f'[{str(i+1)}]::'+' PSK Mismatch for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' Please check PSK ')

def _notify_no_proposal_chosen(i,line,comes_line_phase_1):
    analysis_output.append(f'[{str(i+1)}]::'+' Peer connection: '+comes_line_phase_1+ ' is notifying a no proposal chosen or negotiation mismatch')

def _gw_validation_fail(i,line,comes_line_phase_1,ike_phase_1_type):
    Ike_type = ''
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    if "IKEv1" in ike_phase_1_type:
        Ike_type = "IKE-V1"
        analysis_output.append(f'[{str(i+1)}]::'+' Gateway validation fail for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' Please Check: \n->peer ID \n->certificate settings \n->network ID')
    if "IKEv2" in ike_phase_1_type:
        Ike_type = "IKE-V2"
        analysis_output.append(f'[{str(i+1)}]::'' Gateway validation fail for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' Please Check: \n->peer ID \n->certificate settings \n->network ID')

def _peer_id_fail(i,line,comes_line_phase_1,ike_phase_1_type):
    Ike_type = ''
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    if "IKEv1" in ike_phase_1_type:
        Ike_type = "IKE-V1"
        analysis_output.append(f'[{str(i+1)}]::'+' PEER ID fail for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' Please Check: ->peer ID')
    if "IKEv2" in ike_phase_1_type:
        Ike_type = "IKE-V2"
        analysis_output.append(f'[{str(i+1)}]::'+' PEER ID fail for '+f'{Ike_type}'+ ' Connection '+failure_message.split()[1]+' Please Check: ->peer ID')


def _phase_2_subset(i,line,lines,selectors):
    accepted_proposals = ''
    if i + 1 < len(lines):
        analysis_output.append(f'[{str(i+1)}]:: phase-2 matched by intersection. Accepted proposals are: \n' + selectors + '\n advised to use matching selectors and not sub/super sets')

# phase_2 selector mismatch on responder
def _phase_2_ts_mismatch_responder(i,line,lines,comes_line_phase_1,ike_phase_1_type,selectors):
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    if i + 1 < len(lines):
        if "IKEv1" in ike_phase_1_type:
            Ike_type = "IKE-V1"
            analysis_output.append(f'[{str(i+1)}]:: phase2 selector mismatch for incoming traffic selectors \n' + selectors + '\n advised to check traffic selectors on initiatior for \n' + f'{Ike_type}' + ' connection ' + f'{failure_message}')
        if "IKEv2" in ike_phase_1_type:
            Ike_type = "IKE-V2"
            analysis_output.append(f'[{str(i+1)}]:: phase2 selector mismatch for incoming traffic selectors \n' + selectors + '\n advised to check traffic selectors on initiatior for \n' + f'{Ike_type}' + ' connection ' + f'{failure_message}')

# phase_2 selector mismatch on initiator
def _phase_2_ts_mismatch_initiator(i,line,lines,comes_line_phase_1,ike_phase_1_type):
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    if "IKEv1" in ike_phase_1_type:
        Ike_type = "IKE-V1"
        analysis_output.append(f'[{str(i+1)}]:: phase2 selector mismatch \n advised to check traffic selectors on responder for \n' + f'{Ike_type}' + ' connection ' + f'{failure_message}')
    if "IKEv2" in ike_phase_1_type:
        Ike_type = "IKE-V2"
        analysis_output.append(f'[{str(i+1)}]:: phase2 selector mismatch \n advised to check traffic selectors on responder for \n' + f'{Ike_type}' + ' connection ' + f'{failure_message}')

def _no_policy_configured(i,comes_line_phase_1):
    start_index_failure = comes_line_phase_1.index("comes")
    failure_message = comes_line_phase_1[start_index_failure:]
    analysis_output.append(f'[{str(i+1)}]:: No Policy is Configured for connection'+failure_message)

# check for retrans for phase-1 down
def _phase_1_retrans_check_1(line,lines,i):
    timeout_pattern = r"negotiation timeout, deleting"
    phase1_down_pattern = r"connection expiring due to phase1 down"
    connection_info_pattern = r"(\d+\.\d+\.\d+\.\d+:\d+->\d+\.\d+\.\d+\.\d+:\d+)"
    retransmit_pattern = r"(\w+)\):\s*(\d+\.\d+\.\d+\.\d+:\d+->\d+\.\d+\.\d+\.\d+:\d+)"

    for j in range(max(0, i - 15), min(len(lines), i + 15)):
        if re.search(phase1_down_pattern, lines[j]):
            # Search for connection info in the vicinity
            for k in range(max(0, i - 15), min(len(lines), i + 15)):
                connection_match = re.search(connection_info_pattern, lines[k])
                retransmit_match = re.search(retransmit_pattern, lines[k])
                if connection_match:
                    if retransmit_match:
                        retransmit_type = retransmit_match.group(1)
                        if 'response' in retransmit_type or 'RESPONSE' in retransmit_type:
                            analysis_output.append(f'[{str(k+1)}]::VPN with IP Connection as:: '+connection_match.group(1)+' is down due to negotiation or timeout')
                        else:
                            analysis_output.append(f'[{str(i+1)}]:: VPN with IP Connection as: '+connection_match.group(1)+' is down for Phase-1 due to retransmission failures \n  Possible issues could be: \n -> NAT-T blocked \n -> ISP blocking IKE \n -> port forward misconfig\n -> Network Overlay ID mismatch \n -> Possible PSK mismatch')
                if retransmit_match:
                    retransmit_type = retransmit_match.group(1)
                    retransmit_info = retransmit_match.group(2)
                    if 'response' in retransmit_type or 'RESPONSE' in retransmit_type:
                        analysis_output.append(f'[{str(k+1)}]::Reason for VPN with IP Connection as: '+retransmit_info+' could be for the follwing reasons for error: '+retransmit_type +' \nCheck \n->NAT-4500 blocked \n->authentication failures on the peer ' )
                    else:
                        analysis_output.append(f'[{str(k+1)}]::Reason for VPN with IP Connection as: '+retransmit_info+' for retransmission is for: '+retransmit_type )

def parse_to_table(data_string):
    # Split the string into individual comparisons
    entries = data_string.split(",, ")

    # Initialize lists to store parsed data
    incoming_data = []
    local_data = []

    # Parse each entry and extract incoming and local information
    for entry in entries:
        try:
            incoming_part, local_part = entry.split(" | ")

            # Extract the key and value parts for incoming and local
            incoming_key, incoming_val1, incoming_val2 = eval(incoming_part.split(": ")[1])
            local_key, local_val1, local_val2 = eval(local_part.split(": ")[1])

            # Append the parsed values to the respective lists
            incoming_data.append([incoming_key, incoming_val1, incoming_val2])
            local_data.append([local_key, local_val1, local_val2])
        except:
            return 'Please check if any VPN tunnels are configured for the above connection details'

    # Create DataFrames for Incoming and Local data
    incoming_df = pd.DataFrame(incoming_data, columns=["Key", "Value1", "Value2"])
    local_df = pd.DataFrame(local_data, columns=["Key", "Value1", "Value2"])

    # Combine Incoming and Local data into a single table
    combined_df = pd.concat(
        [incoming_df.add_prefix("Incoming_"), local_df.add_prefix("Local_")], axis=1
    )

    # Pretty-print the table
    return tabulate(combined_df, headers="keys", tablefmt="grid")
    
# Log file in cache
ike_log = read_file(file_name)

ike_parser(ike_log)

def deduplicate_array(arr):
    unique_elements = []
    for item in arr:
        if item not in unique_elements:
            unique_elements.append(item)
    return unique_elements
# Loop through the array to print the analysis
for output in deduplicate_array(analysis_output):
    print(output)
    print('\n')



