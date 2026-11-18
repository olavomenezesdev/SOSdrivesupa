create or replace function public.accept_service_request(p_request_id bigint)
returns public.service_requests
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := auth.uid();
    actor_role text;
    accepted_request public.service_requests;
    claimed_request_id bigint;
begin
    if actor_id is null then
        raise exception 'Authentication required' using errcode = '42501';
    end if;

    select profile.role into actor_role
    from public.profiles profile
    where profile.id = actor_id;
    if actor_role is distinct from 'prestador' then
        raise exception 'Only providers can accept service requests' using errcode = '42501';
    end if;

    insert into public.service_request_acceptance (service_request_id, provider_id)
    values (p_request_id, actor_id)
    on conflict (service_request_id) do nothing
    returning service_request_id into claimed_request_id;

    if claimed_request_id is null then
        raise exception 'Service request is no longer available' using errcode = '23505';
    end if;

    update public.service_requests
    set provider_id = actor_id, status = 'accepted'
    where id = p_request_id and status = 'pending' and provider_id is null
    returning * into accepted_request;

    if not found then
        raise exception 'Service request is no longer available' using errcode = '23505';
    end if;

    return accepted_request;
end;
$$;
