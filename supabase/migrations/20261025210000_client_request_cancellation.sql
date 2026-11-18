create or replace function public.cancel_service_request(p_request_id bigint)
returns public.service_requests
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := auth.uid();
    cancelled_request public.service_requests;
begin
    if actor_id is null then
        raise exception 'Authentication required' using errcode = '42501';
    end if;

    update public.service_requests
    set status = 'cancelled'
    where id = p_request_id
      and user_id = actor_id
      and provider_id is null
      and status = 'pending'
    returning * into cancelled_request;

    if not found then
        raise exception 'Service request cannot be cancelled by this user'
            using errcode = '42501';
    end if;

    return cancelled_request;
end;
$$;

revoke all on function public.cancel_service_request(bigint) from public, anon;
grant execute on function public.cancel_service_request(bigint) to authenticated;
