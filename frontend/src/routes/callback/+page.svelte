<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { userManager } from '$lib/auth';

    onMount(async () => {
        await userManager?.signinRedirectCallback();
        goto('/admin');
    });
</script>