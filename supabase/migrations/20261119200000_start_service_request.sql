create or replace function public.start_service_request(p_request_id bigint)
returns public.service_requests
language plpgsql
security definer
set search_path = ''
as $$
declare
    actor_id uuid := auth.uid();
    actor_role text;
    started_request public.service_requests;
begin
    if actor_id is null then
        raise exception 'Authentication required' using errcode = '42501';
    end if;

    select profile.role into actor_role
    from public.profiles profile
    where profile.id = actor_id;
    if actor_role is distinct from 'prestador' then
        raise exception 'Only providers can start service requests'
            using errcode = '42501';
    end if;

    update public.service_requests as request
    set status = 'in_progress'
    where request.id = p_request_id
      and request.provider_id = actor_id
      and request.status = 'accepted'
    returning request.* into started_request;

    if not found then
        select request.* into started_request
        from public.service_requests request
        where request.id = p_request_id
          and request.provider_id = actor_id
          and request.status = 'in_progress';

        if not found then
            raise exception 'Service request cannot be started by this provider'
                using errcode = '42501';
        end if;
    end if;

    return started_request;
end;
$$;

revoke all on function public.start_service_request(bigint)
    from public, anon, authenticated;
grant execute on function public.start_service_request(bigint)
    to authenticated;
