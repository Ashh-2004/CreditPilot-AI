import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { User, Role } from '../types';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  UserPlus,
  Shield,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Lock,
  User as UserIcon,
  Eye,
  EyeOff
} from 'lucide-react';

interface ManagedUser {
  user_id: number;
  username: string;
  role: Role;
  created_at: string;
}

interface UserManagementViewProps {
  currentUser: User;
}

export const UserManagementView: React.FC<UserManagementViewProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Form state for creating a user
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<Role>('officer');
  const [showPassword, setShowPassword] = useState(false);
  const [creating, setCreating] = useState(false);

  // Deleting state
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getUsers();
      setUsers(res.users || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load user registry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim()) {
      setError('Username cannot be empty.');
      return;
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setCreating(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await api.createUser(newUsername.trim(), newPassword, newRole);
      setActionSuccess(res.message || `User '${newUsername.trim()}' provisioned successfully.`);
      setNewUsername('');
      setNewPassword('');
      setNewRole('officer');
      await fetchUsers();
    } catch (err: any) {
      setError(err?.message || 'Failed to provision user.');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteUser = async (user: ManagedUser) => {
    if (user.username === currentUser.username) {
      setError('Cannot delete your own active administrator account.');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete user "${user.username}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingId(user.user_id);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await api.deleteUser(user.user_id);
      setActionSuccess(res.message || `User '${user.username}' deleted.`);
      await fetchUsers();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete user.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-4 pb-6 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-1.5 flex items-center space-x-1.5">
            <Shield className="w-3.5 h-3.5 text-[#191919]" />
            <span>Administrator access & security governance</span>
          </p>
          <h1 className="font-serif text-4xl sm:text-5xl text-[#191919] tracking-tight leading-[1.1] mb-2.5">
            User access & provisioning
          </h1>
          <p className="text-xs sm:text-sm text-[#191919]/70 font-sans leading-relaxed max-w-2xl">
            In compliance with institutional banking policies, only administrators are authorized to provision new user accounts or manage access roles.
          </p>
        </div>
      </section>

      {/* Notifications */}
      {error && (
        <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 font-sans flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      {actionSuccess && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-sans flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Provision User Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-5">
            <div className="flex items-center space-x-2 pb-3 border-b border-[#E5E5E5]">
              <UserPlus className="w-4 h-4 text-[#191919]" />
              <h2 className="font-serif text-lg text-[#191919]">Provision new user</h2>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-xs font-sans font-medium text-[#191919]/80 mb-1.5">
                  Username
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="e.g. officer_2 or analyst_sharma"
                    required
                    className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-xs font-sans placeholder:text-[#191919]/30 focus:outline-none focus:border-[#191919]"
                  />
                  <UserIcon className="w-3.5 h-3.5 text-[#191919]/40 absolute right-3 top-3" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-sans font-medium text-[#191919]/80 mb-1.5">
                  Initial security password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Minimum 6 characters"
                    required
                    minLength={6}
                    className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-xs font-sans placeholder:text-[#191919]/30 focus:outline-none focus:border-[#191919]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-[#191919]/40 hover:text-[#191919]"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-sans font-medium text-[#191919]/80 mb-1.5">
                  Institutional authorization role
                </label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as Role)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-xs font-sans focus:outline-none focus:border-[#191919]"
                >
                  <option value="officer">Loan Underwriting Officer (Full underwriting & memo access)</option>
                  <option value="viewer">Portfolio Risk Analyst (Read-only analytics access)</option>
                  <option value="admin">Credit Risk Committee / Administrator (Full admin rights)</option>
                </select>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={creating}
                  className="w-full py-2.5 px-4 rounded-lg bg-[#191919] hover:bg-[#333333] text-white text-xs font-sans font-medium transition flex items-center justify-center space-x-2 disabled:opacity-50 shadow-sm"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>{creating ? 'Provisioning account...' : 'Create user account'}</span>
                </button>
              </div>
            </form>

            <p className="text-[11px] text-[#191919]/50 font-sans leading-relaxed pt-2 border-t border-[#E5E5E5]">
              New users can immediately sign in using their provisioned username and security password.
            </p>
          </div>
        </div>

        {/* Right Column: User Registry Table */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-card space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E5]">
              <div>
                <h2 className="font-serif text-lg text-[#191919]">Active user registry</h2>
                <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">
                  Currently active authorized users in the institutional database
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-[11px] px-2.5 py-1 rounded bg-[#F4F3F3] border border-[#E5E5E5] font-sans tabular-nums text-[#191919]">
                  {users.length} {users.length === 1 ? 'user' : 'users'}
                </span>
                <button
                  type="button"
                  onClick={fetchUsers}
                  disabled={loading}
                  className="p-1.5 rounded border border-[#E5E5E5] bg-[#F4F3F3] hover:bg-[#EAEAEA] text-[#191919] transition"
                  title="Refresh user list"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center space-y-2">
                <div className="w-5 h-5 border-2 border-[#191919] border-t-transparent rounded-full animate-spin"></div>
                <p className="text-xs text-[#191919]/50 font-sans">Loading user registry...</p>
              </div>
            ) : users.length === 0 ? (
              <div className="py-12 text-center text-xs text-[#191919]/60 font-sans">
                No users found in database.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-sans">
                  <thead>
                    <tr className="border-b border-[#E5E5E5] text-[#191919]/50 font-medium">
                      <th className="py-2.5 pr-3">ID</th>
                      <th className="py-2.5 px-3">Username</th>
                      <th className="py-2.5 px-3">Role</th>
                      <th className="py-2.5 px-3">Provisioned</th>
                      <th className="py-2.5 pl-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E5E5]/60">
                    {users.map((u) => {
                      const isCurrent = u.username === currentUser.username;
                      return (
                        <tr key={u.user_id} className="hover:bg-[#FAFAFA] transition-colors">
                          <td className="py-3 pr-3 text-[#191919]/50 font-mono text-[11px] tabular-nums">
                            #{u.user_id}
                          </td>
                          <td className="py-3 px-3 font-medium text-[#191919]">
                            <div className="flex items-center space-x-1.5">
                              <span>{u.username}</span>
                              {isCurrent && (
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-sans">
                                  You
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-3">
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded font-sans font-medium uppercase tracking-wider ${
                                u.role === 'admin'
                                  ? 'bg-[#191919] text-white'
                                  : u.role === 'officer'
                                  ? 'bg-[#F4F3F3] text-[#191919] border border-[#E5E5E5]'
                                  : 'bg-[#F4F3F3] text-[#191919]/70'
                              }`}
                            >
                              {u.role}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-[#191919]/60 tabular-nums text-[11px]">
                            {u.created_at || '—'}
                          </td>
                          <td className="py-3 pl-3 text-right">
                            {isCurrent ? (
                              <span className="text-[11px] text-[#191919]/40 italic">Active</span>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleDeleteUser(u)}
                                disabled={deletingId === u.user_id}
                                className="p-1 rounded text-red-600 hover:bg-red-50 transition"
                                title={`Delete user ${u.username}`}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
